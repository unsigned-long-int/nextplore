import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from svc_integration_contracts.models import DataStoreCreateRequest

from integration_service.api.context import get_current_identity
from integration_service.database.exceptions import DataStoreCreateFailed, SecretsCreateFailed
from integration_service.services.data_store import DataStoreService
from integration_service.api.dependencies import get_data_store_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CreateDataStore'])


@router.post(
    '/organizations/{organization_id}/users/{user_id}/datastores',
    status_code=status.HTTP_204_NO_CONTENT
)
async def create_integration(
    organization_id: UUID,
    user_id: UUID,
    payload: DataStoreCreateRequest,
    data_store_service: DataStoreService = Depends(get_data_store_service)
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
        await data_store_service.create_datastore(
            user_identity=user_identity,
            payload=payload,
        )
    except (DataStoreCreateFailed, SecretsCreateFailed) as e:
        logger.error(
            f'Create data store failed with DB error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected create data store error: {str(e)}.',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error while creating data store: {str(e)}'}
        )
    