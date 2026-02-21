import logging
from uuid import UUID
from fastapi import APIRouter, status, HTTPException, Depends
from svc_integration_contracts.models import IntegrationUpdateRequest

from integration_service.api.context import get_current_identity
from integration_service.database.exceptions import IntegrationUpdateFailed, KekKidGetFailed
from integration_service.services.integration import IntegrationService, get_integration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['UpdateIntegration'])


@router.patch(
    '/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def update_integration(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    payload: IntegrationUpdateRequest,
    integration_service: IntegrationService = Depends(get_integration_service)
) -> None:
    user_identity = get_current_identity()
    if user_identity.user_id != user_id or user_identity.organization_id != organization_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )

    try:
        await integration_service.update_integration(
            user_identity=user_identity,
            integration_id=integration_id,
            payload=payload
        )
    except (IntegrationUpdateFailed, KekKidGetFailed) as e:
        logger.error(
            f'Update integration failed with DB error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected update integration error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error while updating integration: {str(e)}'}
        )
