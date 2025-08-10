import asyncio
from fastapi import APIRouter, Depends

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client, get_vector_client
from nextplore_shared.contracts.nextplore_orchestrator_service.user_stats import UserStats
from nextplore_shared.contracts.integration_service.integration_stats_request import IntegrationStatsRequest
from nextplore_shared.contracts.vector_service.vector_stats_request import VectorStatsRequest
from nextplore_shared.cache.service_caches.nextplore_orchestrator_cache.cache import nextplore_orchestrator_service_cache


router = APIRouter()

@router.get('', response_model=UserStats)
async def get_user_stats(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client)
) ->  UserStats:
    cached = await nextplore_orchestrator_service_cache.get_user_stats(user_identity)
    if cached:
        return cached
    
    integr_payload = IntegrationStatsRequest(
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    vec_payload = VectorStatsRequest(
        organization_id=user_identity.organization_id,
        user_id=user_identity.user_id
    )
    integration_stats, vector_stats = await asyncio.gather(
        integration_client.get_integration_stats(integr_payload),
        vector_client.get_vector_stats(vec_payload),
        return_exceptions=True
    )

    response = UserStats(
        integrations_number=integration_stats.integration_count, 
        vectors_number=vector_stats.vector_count
    )
    await nextplore_orchestrator_service_cache.set_user_stats(user_identity, response, ttl=300)
    return response

    

