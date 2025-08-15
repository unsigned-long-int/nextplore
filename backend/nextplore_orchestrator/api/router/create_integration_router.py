import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_create_request import IntegrationCreateRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_create_response import IntegrationCreateResponse
from nextplore_sdk.contracts.integration_service.prepared_integration_create_request import PreparedIntegrationCreateRequest
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from clients.integration import IntegrationCreateRemoteError


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('')
async def create_integration(
    integration_create_request: IntegrationCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationCreateResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    payload = PreparedIntegrationCreateRequest(
        organization_id=org_id,
        user_id=user_id,
        **integration_create_request.model_dump(exclude_none=True)
    )
    try:
        await integration_client.create_integration(payload)
        return IntegrationCreateResponse(success=True)
    except IntegrationCreateRemoteError as e:
        logger.error(
            'Create integration failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Create integration failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {e}'}
        )
