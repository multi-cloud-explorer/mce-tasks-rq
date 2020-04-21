from uuid import uuid4

import pytest
from ddf import G

pytestmark = pytest.mark.django_db(transaction=True, reset_sequences=True)

from mce_django_app import constants
from mce_django_app.models.common import GenericAccount, ResourceType
from mce_django_app.models import azure as models

@pytest.fixture
def subscription(mce_app_generic_account, mce_app_company):
    """Souscription avec ID conforme aux fichiers de fixtures"""

    return models.SubscriptionAzure.objects.create(
        subscription_id="00000000-0000-0000-0000-000000000000",
        name="sub1",
        company=mce_app_company,
        tenant="00000000-0000-0000-0000-000000000000",
        location="francecentral",
        account=mce_app_generic_account
    )


@pytest.fixture
def resource_group(subscription, mce_app_resource_type_azure_group, mce_app_company):

    name = "MY_RG"
    resource_id = f"/subscriptions/{subscription.subscription_id}/resourceGroups/{name}"
    #/providers/{resource_type_azure_group.name}/{name}
    #"id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/MY_RG",
    
    return models.ResourceGroupAzure.objects.create(
        resource_id=resource_id,
        name=name,
        company=mce_app_company,
        resource_type=mce_app_resource_type_azure_group,
        subscription=subscription,
        provider=constants.Provider.AZURE,
        location="francecentral",
    )
