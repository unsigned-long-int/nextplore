import json
from fastapi import APIRouter
from typing import List

from shared.cache.service_caches.vector_cache import vector_service_cache
from shared.contracts.vector_service import VectorProfileResponse, VectorProfileRequest
from api.context import get_current_identity
from database.repositories import VectorRepository


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-profiles', response_model=List[VectorProfileResponse])
async def get_vector_profiles(payload: VectorProfileRequest) -> List[VectorProfileResponse]:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_vector_profiles(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_repo = VectorRepository()

    vector_profiles = await vector_repo.get_vector_profiles(
        integration_id=payload.integration_id
    )
    response = [
        VectorProfileResponse(
            integration_id=vector_profile.integration_id,
            schema_name=vector_profile.schema_name,
            table_name=vector_profile.table_name,
            table_meta=json.loads(vector_profile.table_meta)
        ) for vector_profile in vector_profiles
    ]
    await vector_service_cache.set_vector_profiles(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
