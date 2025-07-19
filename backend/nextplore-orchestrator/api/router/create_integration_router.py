from httpx import HTTPStatusError
from fastapi import APIRouter, Depends

from api.models import IntegrationCreateRequest, IntegrationCreateResponse
from dependencies.authentication import get_active_user
from dependencies.microservices import get_integration_client
from shared.contracts.integration_service import PreparedIntegrationCreateRequest
from shared.identity_service import resolve_user_identity


router = APIRouter()

@router.post('')
async def create_integration(
    integration_create_request: IntegrationCreateRequest,
    user=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationCreateResponse:
    azure_user_id = user.get('oid')
    azure_tenant_id = user.get('tid')
    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)

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
