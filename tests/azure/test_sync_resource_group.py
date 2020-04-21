import pytest
from unittest.mock import patch

from rq.job import JobStatus
import django_rq

import requests

from mce_django_app.models.common import ResourceEventChange, Tag
from mce_django_app.models.azure import ResourceGroupAzure, ResourceAzure
from mce_django_app import constants

pytestmark = pytest.mark.django_db(transaction=True, reset_sequences=True)

# TODO: capture log

@pytest.mark.skip("TODO: requests error (limit, rights)")
def test_azure_sync_resource_group_request_errors():
    """Check sync Azure ResourceGroup - requests errors"""


@pytest.mark.skip("TODO: resource type ou subscription not found ou disable")
def test_azure_sync_resource_group_dependencies():
    """Check sync Azure ResourceGroup - dependencies errors"""
    # msg = f"resource type [{r['type']}] not found - bypass resource [{resource_id}]"


@patch("mce_tasks_rq.azure.get_subscription_and_session")
@patch("requests.Session.get")
def test_azure_sync_resource_group_create(
    session_get_func,
    get_subscription_and_session_func,    
    mock_response_class, 
    json_file, 
    subscription, 
    mce_app_resource_type_azure_group, # Le laisser car nécessaire
    django_rq_worker):
    """Check sync Azure ResourceGroup - Create"""

    data = json_file("resource_group_list.json")
    count_groups = len(data['value'])
    
    get_subscription_and_session_func.return_value = (subscription, requests.Session())    
    session_get_func.return_value = mock_response_class(200, data)

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_group',
        args=[subscription.subscription_id]
    )
    django_rq_worker.work()

    assert job.get_status() == JobStatus.FINISHED

    assert job.result == dict(
        errors=0,
        created=count_groups, 
        updated=0,
        deleted=0
    )

    assert ResourceGroupAzure.objects.count() == count_groups

    # 2 tag dans la 1ère ResourceGroup de resource_group_list.json
    assert Tag.objects.count() == 2 

    assert ResourceEventChange.objects.filter(
        action=constants.EventChangeType.CREATE).count() == count_groups


    # Restart - No changes
    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_group',
        args=[subscription.subscription_id]
    )

    django_rq_worker.work()

    assert job.result == dict(
        errors=0,
        created=0, 
        updated=0,
        deleted=0
    )

@patch("mce_tasks_rq.azure.get_subscription_and_session")
@patch("requests.Session.get")
def test_azure_sync_resource_group_update(
    session_get_func,
    get_subscription_and_session_func,
    mock_response_class, 
    json_file, 
    subscription, 
    mce_app_resource_type_azure_group,
    django_rq_worker):
    """Check sync Azure ResourceGroup - Update"""

    data = json_file("resource_group_list.json")

    get_subscription_and_session_func.return_value = (subscription, requests.Session())

    # --- create
    session_get_func.return_value = mock_response_class(200, data)
    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_group',
        args=[subscription.subscription_id]
    )
    django_rq_worker.work()


    # --- Update one
    data['value'][0]['tags']["testtag"] = "TEST"
    session_get_func.return_value = mock_response_class(200, data)

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_group',
        args=[subscription.subscription_id]
    )
    django_rq_worker.work()
    
    assert job.get_status() == JobStatus.FINISHED
    assert job.result == dict(
        errors=0,
        created=0, 
        updated=1,
        deleted=0
    )

    assert ResourceEventChange.objects.filter(
        action=constants.EventChangeType.UPDATE).count() == 1


@patch("mce_tasks_rq.azure.get_subscription_and_session")
@patch("requests.Session.get")
@pytest.mark.mce_bug
def test_azure_sync_resource_group_delete(
    session_get_func,
    get_subscription_and_session_func,
    mock_response_class, 
    json_file, 
    subscription,     
    mce_app_resource_type_azure_group,
    django_rq_worker):
    """Check sync Azure ResourceGroup - Delete"""

    assert ResourceEventChange.objects.count() == 0
    assert ResourceGroupAzure.objects.count() == 0
    assert ResourceAzure.objects.count() == 0
    
    data = json_file("resource_group_list.json")
    count_groups = len(data['value'])

    get_subscription_and_session_func.return_value = (subscription, requests.Session())

    # --- create
    session_get_func.return_value = mock_response_class(200, data)
    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_group',
        args=[subscription.subscription_id]
    )
    django_rq_worker.work()


    # --- Delete
    session_get_func.return_value = mock_response_class(200, {"value": []})

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_group',
        args=[subscription.subscription_id]
    )
    django_rq_worker.work()

    assert job.get_status() == JobStatus.FINISHED

    # FIXME: bug pour prévoir nombre de delete
    # il affiche 10 alors que j'ai 4 objects (Tag, Event, Group et Resource)
    assert job.result == dict(
        errors=0,
        created=0, 
        updated=0,
        deleted=count_groups
    )

    assert ResourceEventChange.objects.filter(
        action=constants.EventChangeType.DELETE).count() == count_groups

    assert ResourceGroupAzure.objects.count() == 0


