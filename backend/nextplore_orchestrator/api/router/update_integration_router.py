from fastapi import APIRouter, Depends, HTTPException

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_update_request import IntegrationUpdateRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_update_response import IntegrationUpdateResponse
from nextplore_sdk.encryptor.encrypted_fields import ENCRYPTED_FIELDS
from nextplore_sdk.encryptor.encryption import encrypt_secret
from nextplore_sdk.contracts.integration_service.prepared_integration_update_request import PreparedIntegrationUpdateRequest


router = APIRouter()

@router.post('')
async def update_integration(
    integration_update_request: IntegrationUpdateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationUpdateResponse:
    update_args = {
        field: encrypt_secret(value) if field in ENCRYPTED_FIELDS else value for field, value in integration_update_request.model_dump().items()
        if value is not None and field != 'id'
    }
    payload = PreparedIntegrationUpdateRequest(
        integration_id = integration_update_request.id,
        user_id = user_identity.user_id,
        organization_id = user_identity.organization_id,
        update_args = update_args
    )
    try:
        await integration_client.update_integration(payload)
        return IntegrationUpdateResponse(success=True)
    except HTTPException as e:
        return IntegrationUpdateResponse(success=False, message=str(e))
