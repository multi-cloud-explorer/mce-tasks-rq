from rq.job import JobStatus
import django_rq

from mce_django_app.models.common import ResourceType
from mce_django_app.models.tasks import TaskResult

def test_azure_sync_resource_type(django_rq_worker, admin_client):
    """Test create and update ResourceType Task"""

    max_limit = 10

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_type',
        #description="Sync Azure des ResourceType",
        job_timeout='60s',
        kwargs=dict(max_limit=max_limit))

    django_rq_worker.work()

    assert job.get_status() == JobStatus.FINISHED

    assert job.result == dict(
        errors=0,
        created=max_limit, 
        updated=0,
        deleted=0
    )

    assert ResourceType.objects.count() == max_limit

    job = django_rq.enqueue(
        'mce_tasks_rq.azure.sync_resource_type',
        job_timeout='60s',
        kwargs=dict(max_limit=max_limit))

    django_rq_worker.work()

    assert job.get_status() == JobStatus.FINISHED

    assert job.result == dict(
        errors=0,
        created=0, 
        updated=max_limit,
        deleted=0
    )
