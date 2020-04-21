import pytest
from unittest.mock import patch

from rq.job import JobStatus
from rq.job import Job
import django_rq
from django_rq.queues import get_connection, get_queue

import requests

from mce_django_app.models.common import ResourceEventChange, ResourceType
from mce_django_app.models.azure import ResourceAzure
from mce_django_app import constants

@pytest.fixture
def require_resource_types():
    return [
        ResourceType.objects.create(
            name="Microsoft.Compute/virtualMachines",
            provider=constants.Provider.AZURE
        )
    ]

# TODO: tester concurrence si plusieurs worker
# TODO: gérer erreur retry et autre pendant le chargement d'une ressource    
# TODO: gérer product type avec | comme "Type": "Microsoft.Sql/servers/databases|v12.0,user",
# le v12.0,user: devient le kind
# TODO: name avec / comme "name": "samplesqlserver01/sample-azure-mssql"

@patch("mce_azure.core.get_resource_by_id")
@patch("mce_tasks_rq.azure.get_subscription_and_session")
def test_azure_sync_resource_create(
    get_subscription_and_session,
    get_resource_by_id,
    mock_response_class, 
    json_file, 
    subscription,
    resource_group,
    require_resource_types,
    django_rq_worker):
    """Check sync Azure Resource - Create"""

    #data_resource_list = json_file("resource-list.json")
    data = json_file("resource-vm.json")

    get_subscription_and_session.return_value = (subscription, requests.Session())
    get_resource_by_id.return_value = data

    subscription_id = subscription.subscription_id
    resource_id = data['id']
    product_type = data['type']

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource',
        kwargs=dict(
            subscription_id=subscription_id, 
            resource_id=resource_id, 
            product_type=product_type)
    )
    django_rq_worker.work()

    assert job.get_status() == JobStatus.FINISHED

    assert ResourceAzure.objects.count() == 1

    assert job.result == dict(
        pk=ResourceAzure.objects.first().pk,
        created=True, 
        changes=None,
    )

    assert ResourceAzure.objects.count() == 1

    assert ResourceEventChange.objects.filter(
        action=constants.EventChangeType.CREATE).count() == 2 # ResourceAzure + ResourceGroup


@patch("mce_azure.core.get_resources_list")
@patch("mce_azure.core.get_resource_by_id")
@patch("mce_tasks_rq.azure.get_subscription_and_session")
def test_azure_sync_resource_list_create(
    get_subscription_and_session,
    get_resource_by_id,
    get_resources_list,
    mock_response_class, 
    json_file, 
    subscription,
    resource_group,
    require_resource_types,
    django_rq_worker):
    """Check sync Multiple Azure Resource - Create"""

    subscription_id = subscription.subscription_id

    data_resource_list = json_file("resource-list.json")
    data_resource = json_file("resource-vm.json")

    count = len(data_resource_list['value'])
    get_subscription_and_session.return_value = (subscription, requests.Session())
    get_resources_list.return_value = data_resource_list['value']
    get_resource_by_id.return_value = data_resource

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_list',
        args=[subscription_id]
    )
    django_rq_worker.work()

    assert job.get_status() == JobStatus.FINISHED

    """
    print('!!! job._dependency_ids : ', job._dependency_ids)
    print('!!! job._dependency_id : ', job._dependency_id)
    print('!!! job.dependency : ', job.dependency)
    """
    # , connection=queue.connection
    assert "jobs_ids" in job.result
    assert len(job.result["jobs_ids" ]) == 1

    connection = get_connection('default')

    job_id = job.result["jobs_ids"][0]
    job = Job.fetch(job_id, connection=connection)
    """
    print('!!! job._dependency_ids : ', job._dependency_ids)
    print('!!! job._dependency_id : ', job._dependency_id)
    print('!!! job.dependency : ', job.dependency)
    !!! job._dependency_ids :  ['5531ce25-058f-41e9-8262-04905135201e']
    !!! job._dependency_id :  5531ce25-058f-41e9-8262-04905135201e
    !!! job.dependency :  <Job 5531ce25-058f-41e9-8262-04905135201e: mce_tasks_rq.azure.sync_resource_list('00000000-0000-0000-0000-000000000000')>

    """

    assert job.func_name == "mce_tasks_rq.azure.sync_resource"

    assert job.result == dict(
        pk=ResourceAzure.objects.first().pk,
        created=True, 
        changes=None,
    )

