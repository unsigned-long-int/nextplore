import json
from fastapi import APIRouter
from typing import List

from shared.cache.service_caches.vector_cache import vector_service_cache
from shared.contracts.vector_service import VectorMetaRequest, VectorMetaResponse
from api.context import get_current_identity
from database.repositories import VectorRepository


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-metas', response_model=List[VectorMetaResponse])
async def get_vector_metas(payload: VectorMetaRequest) -> List[VectorMetaResponse]:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_vector_metas(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_repo = VectorRepository()

    vector_metas = vector_repo.get_integration_vectors(
        integration_ids=payload.integration_ids
    )
    response = [
        VectorMetaResponse(
            integration_id=vector_meta.integration_id,
            schema_name=vector_meta.schema_name,
            table_name=vector_meta.table_name,
            table_meta=json.loads(vector_meta.table_meta),
            vectors=vector_meta.vector
        ) for vector_meta in vector_metas
    ]
    await vector_service_cache.set_vectors_meta(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
