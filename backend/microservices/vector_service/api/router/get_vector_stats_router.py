from fastapi import APIRouter

from api.context import get_current_identity
from shared.cache.service_caches.vector_cache import vector_service_cache
from shared.contracts.vector_service import VectorStatsRequest, VectorStatsResponse
from database.repositories import VectorRepository


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
   