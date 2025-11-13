import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status

from nextplore_orchestrator.clients.integration import IntegrationUpdateRemoteError
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.clients.integration.models.integration_update_request import IntegrationUpdateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['UpdateIntegration'])


@router.patch('/integrations/{integration_id}', status_code=status.HTTP_202_ACCEPTED)
async def update_integration(
    integration_id: UUID,
    integration_update_request: IntegrationUpdateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> Response:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    try:
        await integration_client.update_integration(
            organization_id=org_id,
            user_id=user_id,
            integration_id=integration_id,
            payload=integration_update_request
        )
        return Response(status_code=status.HTTP_202_ACCEPTED)
    except IntegrationUpdateRemoteError as e:
        logger.error(
            'Integration update failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration update failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

