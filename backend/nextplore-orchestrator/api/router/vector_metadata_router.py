from fastapi import APIRouter, Depends
from typing import List

from dependencies.authentication import get_active_user
from dependencies.microservices import get_vector_client
from shared.contracts.vector_service import VectorMetaRequest
from api.models import VectorMetadata, VectorMetadataRequest

router = APIRouter()

@router.post('', response_model=List[VectorMetadata])
async def get_vectors_metadata(
    vector_metadata_request: VectorMetadataRequest,
    user=Depends(get_active_user),
    vector_client=Depends(get_vector_client)
) -> List[VectorMetadata]:
    payload = VectorMetaRequest(
        integration_ids=[vector_metadata_request.integration_id]
    )
    vector_metas = await vector_client.get_vector_metas(payload)
    return [
        VectorMetadata(
            integration_id=vector_meta.integration_id,
            schema_name=vector_meta.schema_name,
            table_name=vector_meta.table_name,
            table_meta=str(vector_meta.table_meta)
        ) for vector_meta in vector_metas 
    ]
