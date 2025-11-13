import logging
from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from nextplore_orchestrator.clients.integration.models.cert_profile import CertProfile
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.clients.integration import CertGetProfilesRemoteError


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['CertProfiles'])


@router.get('/integrations/certificates/profiles', response_model=List[CertProfile])
async def get_cert_profiles(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> List[CertProfile]:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    try:
        response = await integration_client.get_cert_profiles(
            organization_id=org_id,
            user_id=user_id
        )
        return response
    except CertGetProfilesRemoteError as e:
        logger.error(
            'Certificate get profiles failed (remote)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Certificate get profiles failed (unexpected)',
            extra={'org_id': org_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
