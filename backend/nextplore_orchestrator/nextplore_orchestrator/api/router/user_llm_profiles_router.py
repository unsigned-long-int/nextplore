import logging
from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.clients.integration import DataStoreGetProfilesRemoteError

from svc_integration_contracts.models import UserLlmProfile


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['UserLlmProfiles'])


@router.get('/llm/profiles', response_model=List[UserLlmProfile])
async def get_user_llm_profiles(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> List[UserLlmProfile]:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    try:
        response = await integration_client.get_user_llm_profiles(
            organization_id=org_id,
            user_id=user_id
        )
        return response
    except DataStoreGetProfilesRemoteError as e:
        logger.error(
            'Integration get data store profiles failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration get data store profiles failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
