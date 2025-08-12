import json
from fastapi import APIRouter, Depends
from typing import List

from nextplore_sdk.cache.service_caches.vector_cache.cache import vector_service_cache
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.vector_service.vector_profile_response import VectorProfileResponse
from nextplore_sdk.contracts.vector_service.vector_profile_request import VectorProfileRequest
from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import VectorRepository


router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-profiles', response_model=List[VectorProfileResponse])
async def get_vector_profiles(
    payload: VectorProfileRequest,
    connector: DatabaseBackendConnector = Depends(get_connector)
) -> List[VectorProfileResponse]:
    user_identity = get_current_identity()
    cached = await vector_service_cache.get_vector_profiles(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    vector_repo = VectorRepository(connector)

    vector_profiles = await vector_repo.get_vector_profiles(
        organization_id=user_identity.organization_id,
        user_id=user_identity.user_id,
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
