from fastapi import APIRouter

from api.context import get_current_identity
from database.repositories import VectorRepository
from nextplore_shared.cache.service_caches.vector_cache.cache import vector_service_cache
from nextplore_shared.contracts.vector_service.vector_stats_request import VectorStatsRequest
from nextplore_shared.contracts.vector_service.vector_stats_response import VectorStatsResponse


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-stats', response_model=VectorStatsResponse)
async def get_vector_stats(
    payload: VectorStatsRequest
) -> VectorStatsResponse:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_vector_stats(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_repo = VectorRepository()

    vector_count = await vector_repo.get_vector_count(
        integration_ids=payload.integration_ids
    )
    response = VectorStatsResponse(vector_count=vector_count)
    await vector_service_cache.set_vector_stats(
        user_identity=user_identity,
        request=payload, 
        response=response
    )
    return response
   