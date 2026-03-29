import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client, get_vector_client
from nextplore_orchestrator.api.dependencies.cache import get_orchestrator_cache_service
from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService
from nextplore_orchestrator.clients.integration import DataStoreGetStatsRemoteError
from nextplore_orchestrator.clients.vector import VectorGetStatsRemoteError
from nextplore_orchestrator.api.models.user_stats import UserStats


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['UserStats'])


@router.get('/users/stats', response_model=UserStats)
async def get_user_stats(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
) -> UserStats:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    cached = await cache_service.get_user_stats(user_identity)
    if cached:
        return cached
 
    try:
        datastore_stats, vector_stats = await asyncio.gather(
            integration_client.get_stats(
                organization_id=org_id,
                user_id=user_id
            ),
            vector_client.get_stats(
                organization_id=org_id,
                user_id=user_id
            )
        )

        response = UserStats(
            datastores_number=datastore_stats.datastore_count,
            vectors_number=vector_stats.vector_count
        )
        await cache_service.set_user_stats(user_identity, response, ttl=300)
        return response
    except DataStoreGetStatsRemoteError as e:
        logger.error(
            'Integration get stats failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except VectorGetStatsRemoteError as e:
        logger.error(
            'Vector get stats failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration get stats failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
