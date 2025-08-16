import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_sdk.contracts.vector_service.qdrant_vector_request import QDrantVectorRequest
from nextplore_sdk.contracts.vector_service.qdrant_vector_response import QDrantVectorResponse
from api.context import get_current_identity
from api.dependencies import get_vector_store_service
from services.vector_store_service.exceptions import SearchVectorDBFailed
from services.vector_store_service.store import VectorStoreService
from cache import CacheService, get_cache_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-nearest-qdrant-vectors', response_model=QDrantVectorResponse)
async def get_qdrant_vectors(
    payload: QDrantVectorRequest,
    cache_service: CacheService = Depends(get_cache_service),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
) -> QDrantVectorResponse:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_qdrant_vectors(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        
        vector_ids = await vector_store_service.search_nearest_vectors(user_identity, payload.embedding)
        response = QDrantVectorResponse(
            vector_ids=vector_ids
        )

        await cache_service.set_qdrant_vectors(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except SearchVectorDBFailed as e:
        logger.error(
            f'Get nearest vectors failed with client error: {e}'
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Client error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get nearest vectors failed with unexpected error: {e}'
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
