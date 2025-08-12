import json
from fastapi import APIRouter, Depends
from typing import List

from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.cache.service_caches.vector_cache.cache import vector_service_cache
from nextplore_sdk.contracts.vector_service.vector_meta_request import VectorMetaRequest
from nextplore_sdk.contracts.vector_service.vector_meta_response import VectorMetaResponse
from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import VectorRepository


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-metas', response_model=List[VectorMetaResponse])
async def get_vector_metas(
    payload: VectorMetaRequest,
    connector: DatabaseBackendConnector = Depends(get_connector)
)-> List[VectorMetaResponse]:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_vector_metas(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_repo = VectorRepository(connector)

    vector_metas = await vector_repo.get_vectors(
        organization_id=user_identity.organization_id,
        user_id=user_identity.user_id,
        vector_ids=payload.vector_ids
    )
    response = [
        VectorMetaResponse(
            integration_id=vector_meta.integration_id,
            schema_name=vector_meta.schema_name,
            table_name=vector_meta.table_name,
            table_meta=json.loads(vector_meta.table_meta)
        ) for vector_meta in vector_metas
    ]
    await vector_service_cache.set_vector_metas(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
