from fastapi import APIRouter, Depends
from typing import List

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_vector_client
from nextplore_sdk.contracts.nextplore_orchestrator_service.vector_profile_response import VectorProfileResponse
from nextplore_sdk.contracts.nextplore_orchestrator_service.vector_profile_request import VectorProfileRequest

router = APIRouter()

@router.post('', response_model=List[VectorProfileResponse])
async def get_vectors_profiles(
    vector_profile_request: VectorProfileRequest,
    user=Depends(get_active_user),
    vector_client=Depends(get_vector_client)
) -> List[VectorProfileResponse]:
    vector_profiles = await vector_client.get_vector_profiles(vector_profile_request)
    return [
        VectorProfileResponse(
            integration_id=profile.integration_id,
            schema_name=profile.schema_name,
            table_name=profile.table_name,
            table_meta=str(profile.table_meta)
        ) for profile in vector_profiles 
    ]
