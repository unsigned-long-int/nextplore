import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_orchestrator.clients.integration import IntegrationTestRemoteError
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.models.integration_test_response import IntegrationTestResponse
from nextplore_orchestrator.clients.integration.models.integration_create_request import IntegrationCreateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['Integration'])


@router.post('/integrations/test')
async def test_integration(
    integration_create_request: IntegrationCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationTestResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    
    try:
        await integration_client.test_integration(integration_create_request)
        return IntegrationTestResponse(success=True)
    except IntegrationTestRemoteError as e:
        logger.error(
            'Integration test failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration test failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

