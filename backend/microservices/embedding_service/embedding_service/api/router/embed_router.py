import logging

from fastapi import APIRouter, Depends, HTTPException, status
from svc_embedding_contracts.models import EmbeddingResponse, QueryEmbeddingRequest

from embedding_service.api.context import get_current_identity
from embedding_service.cache import CacheService, get_cache_service
from embedding_service.services.embedding.embedder_factory import dispatch_embedder
from embedding_service.services.embedding.exceptions import (
    EmbeddingFailed,
    MissingEmbedderEngine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/embedding", tags=["Embedding"])


@router.post("/embed", response_model=EmbeddingResponse)
async def embed(
    payload: QueryEmbeddingRequest,
    cache_service: CacheService = Depends(get_cache_service),
) -> EmbeddingResponse:
    user_identity = get_current_identity()
    cached = await cache_service.get_embedding(
        user_identity=user_identity, request=payload
    )
    if cached:
        return cached
    try:
        embedder_cls = dispatch_embedder()
        embedder = embedder_cls()
        embedding = await embedder.generate_embedding(payload.datastream)
        response = EmbeddingResponse(embedding=embedding)

        await cache_service.set_embedding(
            user_identity=user_identity, request=payload, response=response
        )
        return response
    except (EmbeddingFailed, MissingEmbedderEngine) as e:
        logger.error(f"Embedding query failed: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY, detail={"message": str(e)}
        )
    except Exception as e:
        logger.error(f"Embedding error: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
