from fastapi import APIRouter, Depends

from nextplore_sdk.contracts.vector_service.qdrant_vector_request import QDrantVectorRequest
from nextplore_sdk.contracts.vector_service.qdrant_vector_response import QDrantVectorResponse
from api.context import get_current_identity
from services.qdrant.search import search_nearest_vectors
from cache import CacheService, get_cache_service


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-nearest-qdrant-vectors', response_model=QDrantVectorResponse)
async def get_qdrant_vectors(
    payload: QDrantVectorRequest,
    cache_service: CacheService = Depends(get_cache_service)
) -> QDrantVectorResponse:
    user_identity = get_current_identity()
    cached = await cache_service.get_qdrant_vectors(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_ids = await search_nearest_vectors(user_identity, payload.embedding)
    response = QDrantVectorResponse(
        vector_ids=vector_ids
    )

    await cache_service.set_qdrant_vectors(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
