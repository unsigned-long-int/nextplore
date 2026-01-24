import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from svc_integration_contracts.models import IntegrationCreateRequest

from integration_service.api.context import get_current_identity
from integration_service.database.exceptions import IntegrationCreateFailed, SecretsCreateFailed
from integration_service.services.integration import IntegrationService, get_integration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CreateIntegration'])


@router.post(
    '/organizations/{organization_id}/users/{user_id}/integrations',
    status_code=status.HTTP_204_NO_CONTENT
)
async def create_integration(
    organization_id: UUID,
    user_id: UUID,
    payload: IntegrationCreateRequest,
    integration_service: IntegrationService = Depends(get_integration_service)
) -> None:
    user_identity = get_current_identity()

    if organization_id != user_identity.organization_id or user_id != user_identity.user_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )

    try:
        await integration_service.create_integration(
            user_identity=user_identity,
            payload=payload,
        )
    except (IntegrationCreateFailed, SecretsCreateFailed) as e:
        logger.error(
            f'Create integration failed with DB error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected create integration error: {str(e)}.',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error while creating integration: {str(e)}'}
        )
    