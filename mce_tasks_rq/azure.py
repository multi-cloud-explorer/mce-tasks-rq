import jsonpatch

from rq import get_current_job
import django_rq

from mce_azure.utils import get_access_token
from mce_azure import core as cli
from mce_azure.core import PROVIDERS

from mce_django_app import constants
from mce_django_app.models.common import ResourceEventChange, Tag, ResourceType
from mce_django_app.models.tasks import TaskResult
from mce_django_app.models import azure as models

from mce_tasks_rq.utils import get_job_logger
from mce_tasks_rq.decorators import mce_job

logger = get_job_logger(__name__)

def get_subscription_and_session(subscription_id):
    # TODO: raise if active=False
    subscription = models.SubscriptionAzure.objects.get(subscription_id=subscription_id)
    auth = subscription.get_auth()
    token = get_access_token(**auth)
    session = cli.get_session(token=token['access_token'])
    return subscription, session


def create_event_change_update(old_obj, new_resource):
    """UPDATE Event for ResourceAzure and ResourceGroupAzure"""

    new_obj = new_resource.to_dict(exclude=["created", "updated"])

    patch = jsonpatch.JsonPatch.from_diff(old_obj, new_obj)

    if patch.patch:
        msg = f"create event change update for {old_obj['resource_id']}"
        logger.info(msg)

        return ResourceEventChange.objects.create(
            action=constants.EventChangeType.UPDATE,
            content_object=new_resource,
            changes=list(patch),
            old_object=old_obj,
            new_object=new_obj,
            diff=None,
        )


def create_event_change_delete(queryset):
    """DELETE Event for ResourceAzure and ResourceGroupAzure"""

    for doc in queryset:
        ResourceEventChange.objects.create(
            action=constants.EventChangeType.DELETE,
            content_object=doc,
            old_object=doc.to_dict(exclude=['created', 'updated']),
        )

@mce_job
def sync_resource_group(subscription_id):

    # TODO: catch error
    subscription, session = get_subscription_and_session(subscription_id)
    company = subscription.company

    # TODO: catch error
    resources_groups = cli.get_resourcegroups_list(subscription_id, session=session)

    _created = 0
    _updated = 0
    _errors = 0
    _deleted = 0

    found_ids = []

    for r in resources_groups:

        resource_id = r['id'].lower()
        found_ids.append(resource_id)

        _type = ResourceType.objects.filter(
            name__iexact=r['type'], provider=constants.Provider.AZURE
        ).first()

        if not _type:
            _errors += 1
            msg = f"resource type [{r['type']}] not found - bypass resource [{resource_id}]"
            logger.error(msg)
            continue

        # TODO: ajouter autres champs ?
        metas = r.get('properties', {}) or {}

        tags_objects = []

        # TODO: events et logs
        tags = r.get('tags', {}) or {}
        for k, v in tags.items():
            tag, created = Tag.objects.update_or_create(
                name=k, provider=constants.Provider.AZURE, defaults=dict(value=v)
            )
            tags_objects.append(tag)
            # if created: todo event tag

        old_resource = models.ResourceGroupAzure.objects.filter(resource_id=resource_id).first()
        old_object = None
        if old_resource:
            old_object = old_resource.to_dict(exclude=["created", "updated"])

        new_resource, created = models.ResourceGroupAzure.objects.update_or_create(
            resource_id=resource_id,
            defaults=dict(
                name=r['name'],  # TODO: lower ?
                subscription=subscription,
                company=company,
                resource_type=_type,
                location=r['location'],
                provider=constants.Provider.AZURE,
                metas=metas,
            ),
        )
        if tags_objects:
            new_resource.tags.set(tags_objects)

        if created:
            _created += 1
        else:
            changes = create_event_change_update(old_object, new_resource)
            if changes:
                _updated += 1

    logger.info(
        "sync - azure - ResourceGroupAzure - _errors[%s] - created[%s]- updated[%s]"
        % (_errors, _created, _updated)
    )

    # Create events delete
    qs = models.ResourceGroupAzure.objects.exclude(
        resource_id__in=found_ids, subscription=subscription
    )
    create_event_change_delete(qs)

    # Mark for deleted
    # TODO: delegate tasks ?
    _deleted, objects = models.ResourceGroupAzure.objects.exclude(
        resource_id__in=found_ids, subscription=subscription
    ).delete()

    #print()
    #print('----------------------------------------------')
    #for o in objects: print(o, type(o))
    #print('----------------------------------------------')

    logger.info(f"mark for deleted. [{_deleted}] old ResourceGroupAzure")

    # TODO: répercuter deleted sur les ressources rattachés ?
    # doc.resourceazure_set.all()
    # voir si déjà fait au niveau resource !

    return dict(errors=_errors, created=_created, updated=_updated, deleted=_deleted)


@mce_job
def sync_resource(subscription_id=None, resource_id=None, product_type=None):

    # TODO: récupérer le token de session ?
    subscription, session = get_subscription_and_session(subscription_id)
    company = subscription.company

    logger.debug(f"start for resource [{resource_id}]")

    if '|' in product_type:
        product_type = product_type.split('|')[0]

    _type = ResourceType.objects.filter(
        name__iexact=product_type, provider=constants.Provider.AZURE
    ).first()

    if not _type:
        msg = f"resource type [{product_type}] not found - bypass resource [{resource_id}]"
        logger.error(msg)
        raise Exception(msg)

    group_name = resource_id.split('/')[4]
    group_id = f"/subscriptions/{subscription.subscription_id}/resourceGroups/{group_name}"
    # TODO: ajout company et subscription au filtre
    group = models.ResourceGroupAzure.objects.filter(resource_id__iexact=group_id).first()

    if not group:
        msg = f"resource group [{group_id}] not found - bypass resource [{resource_id}]"
        logger.error(msg)
        raise Exception(msg)

    try:
        resource = cli.get_resource_by_id(resource_id, session=session)
    except Exception as err:
        msg = f"fetch resource {resource_id} error : {err}"
        logger.exception(msg)
        raise Exception(msg)

    metas = resource.get('properties', {}) or {}

    tags_objects = []

    datas = dict(
        name=resource['name'],
        subscription=subscription,
        company=company,
        resource_type=_type,
        location=resource.get('location'),
        provider=constants.Provider.AZURE,
        resource_group=group,
        metas=metas,
    )

    if resource.get('sku'):
        datas['sku'] = resource.get('sku')

    if resource.get('kind'):
        datas['kind'] = resource.get('kind')

    tags = resource.get('tags', {}) or {}
    for k, v in tags.items():
        tag, created = Tag.objects.update_or_create(
            name=k, provider=constants.Provider.AZURE, defaults=dict(value=v)
        )
        tags_objects.append(tag)
        # if created: todo event tag

    old_resource = models.ResourceAzure.objects.filter(resource_id=resource_id).first()
    old_object = None
    if old_resource:
        old_object = old_resource.to_dict(exclude=["created", "updated"])

    new_resource, created = models.ResourceAzure.objects.update_or_create(
        resource_id=resource_id, defaults=datas
    )

    if tags_objects:
        new_resource.tags.set(tags_objects)

    result = {"pk": new_resource.pk, "created": created, "changes": None}

    changes = None
    if not created:
        changes = create_event_change_update(old_object, new_resource)

    if changes:
        result["changes"] = changes.to_dict(exclude=['created', 'updated'])

    return result


@mce_job
def sync_resource_list(subscription_id):

    """
    TODO: faire une version qui créer une async_task pour chaque resource
    1. fetch resource by id
    2. db + event
    > pas de gevent dans ce cas car parallélisme assurer par django-q
    """

    # TODO: catch error
    subscription, session = get_subscription_and_session(subscription_id)

    _created = 0
    _updated = 0
    _errors = 0
    _deleted = 0

    found_ids = []
    jobs_ids = []

    current_job = get_current_job()

    for i, r in enumerate(cli.get_resources_list(subscription_id, session)):

        resource_id = r['id'] #TODO: ? .lower()
        found_ids.append(resource_id)

        logger.debug(f"{i} - create or update azure resource [{resource_id}]")

        job = sync_resource.delay(
            depends_on=current_job,
            subscription_id=subscription_id, 
            resource_id=resource_id,
            product_type=r.get('type')
        )
        jobs_ids.append(job.id)

    result = {"jobs_ids": jobs_ids}

    #logger.info(
    #    "sync - azure - ResourceAzure - errors[%s] - created[%s]- updated[%s]"
    #    % (_errors, _created, _updated)
    #)

    # Create events delete
    qs = models.ResourceAzure.objects.exclude(
        resource_id__in=found_ids, subscription=subscription
    )
    create_event_change_delete(qs)

    qs = models.ResourceAzure.objects.exclude(
        resource_id__in=found_ids, subscription=subscription
    )
    _deleted, objects = qs.delete()

    logger.info("mark for deleted. [%s] old ResourceAzure" % _deleted)

    #return dict(errors=_errors, created=_created, updated=_updated, deleted=_deleted)
    return result


"""
TODO: intégrer record TaskResult dans decorateur qui gère concurrence
current_job = get_current_job()
print("job.id           : ", job.id)
print("job.key          : ", job.key)
print("job.is_failed    : ", job.is_failed)
print("job.get_status() : ", job.get_status()) # queued, started, deferred, finished, and failed
print("job.result       : ", job.result, type(job.result))
TaskResult.objects.create()
"""

@mce_job
def sync_resource_type(max_limit=None):
    """Azure ResourceType Sync"""

    _created = 0
    _updated = 0
    _errors = 0
    _deleted = 0

    # FIXME: use batch insert !
    
    for i, (k, v) in enumerate(PROVIDERS.items(), start=1):
        if max_limit and i > max_limit:
            break

        logger.debug(f"{i} - create or update resource type [{k}]")

        r, created = ResourceType.objects.update_or_create(
            name=k, defaults=dict(provider=constants.Provider.AZURE)
        )

        if created:
            _created += 1
        else:
            _updated += 1

    logger.info(
        "sync - azure - ResourceType - errors[%s] - created[%s]- updated[%s]"
        % (_errors, _created, _updated)
    )

    return dict(errors=_errors, created=_created, updated=_updated, deleted=_deleted)


# 0 0 * * * Daily
# 0 * * * * hourly

JOBS = [
    (sync_resource_type, "*/15 * * * *"), 
    (sync_resource_group, "*/15 * * * *"),
    (sync_resource_list, "*/30 * * * *"),
]

def create_schedule_jobs(scheduler=None):
    scheduler = scheduler or django_rq.get_scheduler('default')

    # depends_on pour scheduler. voir PR 225
    for func, cron in JOBS:
        scheduler.cron(
            cron,
            func=func,
            repeat=None,
            #queue_name=queue_name,
            #use_local_timezone=True
        )

def create_once_jobs():
    for func, _ in JOBS:
        func.delay()

