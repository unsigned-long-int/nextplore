from fastapi import APIRouter, Depends
from typing import List

from shared.contracts.integration_service import PreparedIntegrationGetRequest
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from api.models import IntegrationProfile

router = APIRouter()

@router.get('', response_model=List[IntegrationProfile])
async def get_integrations(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) ->  List[IntegrationProfile]:
    payload = PreparedIntegrationGetRequest(
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )

    response = await integration_client.get_integrations(payload)
    return response
