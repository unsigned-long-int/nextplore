import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.vector_service.vector_stats_request import VectorStatsRequest
from nextplore_sdk.contracts.vector_service.vector_stats_response import VectorStatsResponse
from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import VectorRepository
from database.exceptions import VectorCountGetFailed
from cache import CacheService, get_cache_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-stats', response_model=VectorStatsResponse)
async def get_vector_stats(
    payload: VectorStatsRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> VectorStatsResponse:
    try:
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
    except VectorCountGetFailed as e:
        logger.error(
            f'Get vector stats failed with DB error: {e}.', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(f'Unexpected get vector stats error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

   