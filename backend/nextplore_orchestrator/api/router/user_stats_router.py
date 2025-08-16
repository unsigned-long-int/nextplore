import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client, get_vector_client
from api.dependencies.cache import get_orchestrator_cache_service
from cache.orchestrator_cache import OrchestratorCacheService
from clients.integration import IntegrationGetStatsRemoteError
from clients.vector import VectorGetStatsRemoteError
from nextplore_sdk.contracts.nextplore_orchestrator_service.user_stats import UserStats
from nextplore_sdk.contracts.integration_service.integration_stats_request import IntegrationStatsRequest
from nextplore_sdk.contracts.vector_service.vector_stats_request import VectorStatsRequest


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get('', response_model=UserStats)
async def get_user_stats(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
) ->  UserStats:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    cached = await cache_service.get_user_stats(user_identity)
    if cached:
        return cached
    
    integr_payload = IntegrationStatsRequest(
        user_id=user_id,
        organization_id=org_id
    )
    vec_payload = VectorStatsRequest(
        organization_id=org_id,
        user_id=user_id
    )
    try:
        integration_stats, vector_stats = await asyncio.gather(
            integration_client.get_integration_stats(integr_payload),
            vector_client.get_vector_stats(vec_payload),
            return_exceptions=True
        )

        response = UserStats(
            integrations_number=integration_stats.integration_count, 
            vectors_number=vector_stats.vector_count
        )
        await cache_service.set_user_stats(user_identity, response, ttl=300)
        return response
    except IntegrationGetStatsRemoteError as e:
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


    

