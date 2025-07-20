from fastapi import APIRouter

from shared.contracts.embedding_service import QueryEmbeddingRequest, EmbeddingResponse
from shared.cache.service_caches.embedding_cache import embedding_service_cache
from api.context import get_current_identity
from api.handlers import handle_query_embedding


router = APIRouter(prefix='/v1/embedding', tags=['Embedding'])

@router.post('/embed', response_model=EmbeddingResponse)
async def embed(payload: QueryEmbeddingRequest) -> EmbeddingResponse:
    user_identity = get_current_identity()
    cached = await embedding_service_cache.get_embedding(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    response = handle_query_embedding(payload)
    await embedding_service_cache.set_embedding(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
