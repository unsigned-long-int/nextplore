import json
from fastapi import APIRouter
from typing import List

from nextplore_shared.cache.service_caches.vector_cache.cache import vector_service_cache
from nextplore_shared.contracts.vector_service.qdrant_vector_request import QDrantVectorRequest
from nextplore_shared.contracts.vector_service.qdrant_vector_response import QDrantVectorResponse
from api.context import get_current_identity
from services.qdrant.search import search_nearest_vectors


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-nearest-qdrant-vectors', response_model=QDrantVectorResponse)
async def get_qdrant_vectors(payload: QDrantVectorRequest) -> QDrantVectorResponse:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_qdrant_vectors(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_ids = await search_nearest_vectors(user_identity, payload.embedding)
    response = QDrantVectorResponse(
        vector_ids=vector_ids
    )
    print('router qqdrant response')
    print(response)

    await vector_service_cache.set_qdrant_vectors(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
