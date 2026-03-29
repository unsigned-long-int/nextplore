import logging
from uuid import UUID
from fastapi import APIRouter, status, HTTPException, Depends
from integration_service.api.context import get_current_identity
from integration_service.database.exceptions import DataStoreUpdateFailed, KekKidGetFailed
from integration_service.services.data_store import DataStoreService
from integration_service.api.dependencies import get_data_store_service

from svc_integration_contracts.models import DataStoreUpdateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['UpdateDataStore'])


@router.patch(
    '/organizations/{organization_id}/users/{user_id}/datastores/{datastore_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def update_datastore(
    organization_id: UUID,
    user_id: UUID,
    datastore_id: UUID,
    payload: DataStoreUpdateRequest,
    datastore_service: DataStoreService = Depends(get_data_store_service)
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
        await datastore_service.update_datastore(
            user_identity=user_identity,
            datastore_id=datastore_id,
            payload=payload
        )
    except (DataStoreUpdateFailed, KekKidGetFailed) as e:
        logger.error(
            f'Update data store failed with DB error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected update data_store error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error while updating data_store: {str(e)}'}
        )
