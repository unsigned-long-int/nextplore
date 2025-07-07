import uuid
from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from services.database.repositories import VectorRepository
from services.authentication import get_active_user
from api.models import VectorMetadata, VectorMetadataRequest

router = APIRouter()

@router.post('', response_model=List[VectorMetadata])
def get_vectors_metadata(
    vector_metadata_request: VectorMetadataRequest,
    user=Depends(get_active_user)
) -> List[VectorMetadata]:
    print(vector_metadata_request)
    vector_repo = VectorRepository()
    
    vectors_orm = vector_repo.get_integration_vectors([vector_metadata_request.integration_id])
    return [
        VectorMetadata(
            integration_id=vector.integration_id,
            schema_name=vector.schema_name,
            table_name=vector.table_name,
            table_meta=vector.table_meta
        ) for vector in vectors_orm 
    ]
