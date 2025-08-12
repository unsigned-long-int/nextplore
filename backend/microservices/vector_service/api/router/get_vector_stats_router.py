from fastapi import APIRouter, Depends

from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.vector_service.vector_stats_request import VectorStatsRequest
from nextplore_sdk.contracts.vector_service.vector_stats_response import VectorStatsResponse
from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import VectorRepository
from cache import CacheService, get_cache_service


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-stats', response_model=VectorStatsResponse)
async def get_vector_stats(
    payload: VectorStatsRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> VectorStatsResponse:
    user_identity = get_current_identity()
    cached = await cache_service.get_vector_stats(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_repo = VectorRepository(connector)

    vector_count = await vector_repo.get_vector_count(
        organization_id=payload.organization_id,
        user_id=payload.user_id
    )
    response = VectorStatsResponse(vector_count=vector_count)
    await cache_service.set_vector_stats(
        user_identity=user_identity,
        request=payload, 
        response=response
    )
    return response
   