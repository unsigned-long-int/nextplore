from fastapi import APIRouter, Depends

from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import VectorRepository
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.cache.service_caches.vector_cache.cache import vector_service_cache
from nextplore_sdk.contracts.vector_service.vector_stats_request import VectorStatsRequest
from nextplore_sdk.contracts.vector_service.vector_stats_response import VectorStatsResponse


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-stats', response_model=VectorStatsResponse)
async def get_vector_stats(
    payload: VectorStatsRequest,
    connector: DatabaseBackendConnector = Depends(get_connector)
) -> VectorStatsResponse:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_vector_stats(
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
    await vector_service_cache.set_vector_stats(
        user_identity=user_identity,
        request=payload, 
        response=response
    )
    return response
   