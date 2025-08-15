import logging
from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from nextplore_sdk.contracts.integration_service.prepared_integration_get_request import PreparedIntegrationGetRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_profile import IntegrationProfile
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from clients.integration import IntegrationGetProfilesRemoteError


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get('', response_model=List[IntegrationProfile])
async def get_integrations(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) ->  List[IntegrationProfile]:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    payload = PreparedIntegrationGetRequest(
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    try:
        response = await integration_client.get_integrations(payload)
        return response
    except IntegrationGetProfilesRemoteError as e:
        logger.error(
            'Integration get profiles failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration get profiles failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
