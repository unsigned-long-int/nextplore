import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from svc_integration_contracts.models import DataStoreStatsResponse

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from integration_service.cache import CacheService, get_cache_service
from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.database.exceptions import DataStoreGetFailed
from integration_service.database.repositories import DataStoreRepository


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['DataStoreStats'])


@router.get('/organizations/{organization_id}/users/{user_id}/datastores/stats', response_model=DataStoreStatsResponse)
async def get_datastore_stats(
    organization_id: UUID,
    user_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> DataStoreStatsResponse:
    user_identity = get_current_identity()
    if user_id != user_identity.user_id or organization_id != user_identity.organization_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )
    
    datastore_repo = DataStoreRepository(backend_connector)

    try:
        cached = await cache_service.get_datastore_stats(
            user_identity=user_identity
        )
        if cached:
            return cached

        datastore_ids = await datastore_repo.get_user_datastore_ids(
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id
        )

        response = DataStoreStatsResponse(
            datastore_ids=datastore_ids,
            datastore_count=len(datastore_ids)
        )
        await cache_service.set_datastore_stats(
            user_identity=user_identity,
            response=response
        )
        return response
    except DataStoreGetFailed as e:
        logger.error(
            f'Get data store stats request failed with DB error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get data store stats failed with unexpected error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )