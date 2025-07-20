from httpx import HTTPStatusError
from fastapi import APIRouter, Depends

from api.models import IntegrationCreateRequest, IntegrationCreateResponse
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from shared.contracts.integration_service import PreparedIntegrationCreateRequest


router = APIRouter()

@router.post('')
async def create_integration(
    integration_create_request: IntegrationCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationCreateResponse:
    payload = PreparedIntegrationCreateRequest(
        organization_id=user_identity.organization_id,
        user_id=user_identity.user_id,
        **integration_create_request.model_dump()
    )
    try:
        await integration_client.create_integration(payload)
        return IntegrationCreateResponse(success=True)
    except HTTPStatusError as e:
        return IntegrationCreateResponse(success=False, message=str(e.detail))
