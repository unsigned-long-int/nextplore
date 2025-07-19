from fastapi import APIRouter

from shared.cache.service_caches.vector_cache import vector_service_cache
from shared.contracts.vector_service import VectorMetaRequest, VectorStatsResponse
from database.repositories import VectorRepository


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-stats', response_model=VectorStatsResponse)
async def get_vector_stats(payload: VectorMetaRequest) -> VectorStatsResponse:
    cached = await vector_service_cache.get_vector_stats(payload)
    if cached:
        return cached
    
    vector_repo = VectorRepository()

    vector_count = vector_repo.get_vector_count(
        integration_ids=payload.integration_ids
    )
    response = VectorStatsResponse(vector_count=vector_count)
    await vector_service_cache.set_vector_stats(
        payload, 
        response
    )
    return response
   