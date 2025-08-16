import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_vector_client
from clients.vector import VectorGetProfilesRemoteError
from nextplore_sdk.contracts.nextplore_orchestrator_service.vector_profile_response import VectorProfileResponse
from nextplore_sdk.contracts.nextplore_orchestrator_service.vector_profile_request import VectorProfileRequest


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('', response_model=List[VectorProfileResponse])
async def get_vectors_profiles(
    vector_profile_request: VectorProfileRequest,
    user_identity=Depends(get_active_user),
    vector_client=Depends(get_vector_client)
) -> List[VectorProfileResponse]:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        vector_profiles = await vector_client.get_vector_profiles(vector_profile_request)
        return [
            VectorProfileResponse(
                integration_id=profile.integration_id,
                schema_name=profile.schema_name,
                table_name=profile.table_name,
                table_meta=str(profile.table_meta)
            ) for profile in vector_profiles 
        ]
    
    except VectorGetProfilesRemoteError as e:
        logger.error(
            'Vector get profiles failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Vector get profiles failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

