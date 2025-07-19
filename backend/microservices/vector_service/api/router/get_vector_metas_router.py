import json
from fastapi import APIRouter
from typing import List

from shared.contracts.vector_service import VectorMetaRequest, VectorMetaResponse
from database.repositories import VectorRepository


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-metas', response_model=List[VectorMetaResponse])
def get_vector_metas(payload: VectorMetaRequest) -> List[VectorMetaResponse]:
    vector_repo = VectorRepository()

    vector_metas = vector_repo.get_integration_vectors(
        integration_ids=payload.integration_ids
    )
    return [
        VectorMetaResponse(
            integration_id=vector_meta.integration_id,
            schema_name=vector_meta.schema_name,
            table_name=vector_meta.table_name,
            table_meta=json.loads(vector_meta.table_meta),
            vectors=vector_meta.vector
        ) for vector_meta in vector_metas
    ]