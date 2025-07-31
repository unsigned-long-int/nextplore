from fastapi import APIRouter, Depends

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client, get_vector_client
from shared.contracts.nextplore_orchestrator_service import UserStats
from shared.contracts.integration_service import IntegrationStatsRequest
from shared.contracts.vector_service import VectorStatsRequest
from shared.cache.service_caches.nextplore_orchestrator_cache import nextplore_orchestrator_service_cache


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
    
    payload = IntegrationStatsRequest(
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    integration_stats = await integration_client.get_integration_stats(payload)

    payload = VectorStatsRequest(
        integration_ids=integration_stats.integration_ids
    )
    vector_stats = await vector_client.get_vector_stats(payload)

    response = UserStats(
        integrations_number=integration_stats.integration_count, 
        vectors_number=vector_stats.vector_count
    )
    await nextplore_orchestrator_service_cache.set_user_stats(user_identity, response, ttl=300)
    return response

    

