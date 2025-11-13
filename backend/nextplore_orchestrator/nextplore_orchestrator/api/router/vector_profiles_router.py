import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_vector_client
from nextplore_orchestrator.clients.vector import VectorGetProfilesRemoteError
from nextplore_orchestrator.clients.vector.models.vector_profile_response import VectorProfileResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['VectorProfiles'])


@router.get('/integrations/{integration_id}/vectors/profiles', response_model=List[VectorProfileResponse])
async def get_vector_profiles(
    integration_id: UUID,
    user_identity=Depends(get_active_user),
    vector_client=Depends(get_vector_client)
) -> List[VectorProfileResponse]:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        vector_profiles = await vector_client.get_profiles(
            organization_id=org_id,
            user_id=user_id,
            integration_id=integration_id
        )
        return vector_profiles
    
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

