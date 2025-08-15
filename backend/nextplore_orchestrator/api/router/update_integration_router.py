import logging
from fastapi import APIRouter, Depends, HTTPException, status

from clients.integration import IntegrationUpdateRemoteError
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_update_request import IntegrationUpdateRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_update_response import IntegrationUpdateResponse
from nextplore_sdk.encryptor.encrypted_fields import ENCRYPTED_FIELDS
from nextplore_sdk.encryptor.encryption import encrypt_secret
from nextplore_sdk.contracts.integration_service.prepared_integration_update_request import PreparedIntegrationUpdateRequest


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('')
async def update_integration(
    integration_update_request: IntegrationUpdateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationUpdateResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    update_args = {
        field: encrypt_secret(value) if field in ENCRYPTED_FIELDS else value for field, value in integration_update_request.model_dump().items()
        if value is not None and field != 'id'
    }
    payload = PreparedIntegrationUpdateRequest(
        integration_id = integration_update_request.id,
        user_id = user_id,
        organization_id = org_id,
        update_args = update_args
    )
    try:
        await integration_client.update_integration(payload)
        return IntegrationUpdateResponse(success=True)
    except IntegrationUpdateRemoteError as e:
        logger.error(
            'Integration update failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration update failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

