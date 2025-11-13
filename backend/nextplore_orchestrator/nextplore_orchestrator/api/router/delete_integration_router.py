import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status

from nextplore_orchestrator.clients.integration import IntegrationDeleteRemoteError
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.dependencies.cache import get_orchestrator_cache_service
from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['DeleteIntegration'])


@router.delete('/integrations/{integration_id}', status_code=status.HTTP_202_ACCEPTED)
async def delete_integration(
    integration_id: UUID,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
) -> Response:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    try:
        await integration_client.delete_integration(
            organization_id=org_id,
            user_id=user_id,
            integration_id=integration_id
        )
        await cache_service.delete_user_stats(user_identity)
        return Response(status_code=status.HTTP_202_ACCEPTED)
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
