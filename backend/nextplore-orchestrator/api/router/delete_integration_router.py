from httpx import HTTPStatusError
from fastapi import APIRouter, Depends

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from shared.contracts.integration_service import PreparedIntegrationDeleteRequest
from api.models import IntegrationDeleteRequest, IntegrationDeleteResponse


router = APIRouter()

@router.post('')
async def delete_integration(
    integration_delete_request: IntegrationDeleteRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationDeleteResponse:

    payload = PreparedIntegrationDeleteRequest(
        integration_id=integration_delete_request.id,
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    try:
        await integration_client.delete_integration(payload)
        return IntegrationDeleteResponse(success=True)
    except HTTPStatusError as e:
        return IntegrationDeleteResponse(success=False, message=str(e))
