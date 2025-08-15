import logging
from fastapi import APIRouter, Depends, HTTPException, status

from clients.integration import IntegrationDeleteRemoteError
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from api.dependencies.cache import get_orchestrator_cache_service
from cache.orchestrator_cache import OrchestratorCacheService
from nextplore_sdk.contracts.integration_service.prepared_integration_delete_request import PreparedIntegrationDeleteRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_delete_request import IntegrationDeleteRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_delete_response import IntegrationDeleteResponse


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('')
async def delete_integration(
    integration_delete_request: IntegrationDeleteRequest,
    user_identity = Depends(get_active_user),
    integration_client = Depends(get_integration_client),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
) -> IntegrationDeleteResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    payload = PreparedIntegrationDeleteRequest(
        integration_id=integration_delete_request.id,
        user_id=user_id,
        organization_id=org_id
    )
    try:
        await integration_client.delete_integration(payload)
        await cache_service.delete_user_stats(user_identity)
        return IntegrationDeleteResponse(success=True)
    except IntegrationDeleteRemoteError as e:
        logger.error(
            'Delete integration failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )    
    except Exception as e:
        logger.error(
            'Delete integration failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {e}'}
        )
