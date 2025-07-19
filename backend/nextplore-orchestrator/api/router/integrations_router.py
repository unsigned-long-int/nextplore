from fastapi import APIRouter, Depends
from typing import List

from shared.contracts.integration_service import PreparedIntegrationGetRequest
from dependencies.authentication import get_active_user
from dependencies.microservices import get_integration_client
from shared.identity_service import resolve_user_identity
from api.models import IntegrationProfile

router = APIRouter()

@router.get('', response_model=List[IntegrationProfile])
async def get_integrations(
    user=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) ->  List[IntegrationProfile]:
    azure_user_id = user.get('oid')
    azure_tenant_id = user.get('tid')

    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)

    payload = PreparedIntegrationGetRequest(
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )

    response = await integration_client.get_integrations(payload)
    return response
