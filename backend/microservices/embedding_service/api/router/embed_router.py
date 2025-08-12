import logging
from fastapi import APIRouter, HTTPException, status, Depends

from nextplore_sdk.contracts.embedding_service.query_embedding_request import QueryEmbeddingRequest
from nextplore_sdk.contracts.embedding_service.embedding_response import EmbeddingResponse
from cache import CacheService, get_cache_service
from api.context import get_current_identity
from api.handlers import handle_query_embedding
from services.exceptions import MissingEmbedderEngine, EmbeddingFailed


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/embedding', tags=['Embedding'])

@router.post('/embed', response_model=EmbeddingResponse)
async def embed(
    payload: QueryEmbeddingRequest,
    cache_service: CacheService = Depends(get_cache_service)
) -> EmbeddingResponse:
    user_identity = get_current_identity()
    cached = await cache_service.get_embedding(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    try:
        response = await handle_query_embedding(payload)
        await cache_service.set_embedding(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except (EmbeddingFailed, MissingEmbedderEngine) as e:
        logger.error(f'Embedding query failed: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Embedding error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
