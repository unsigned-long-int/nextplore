import logging
from fastapi import APIRouter, status, HTTPException, Depends


from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import (
    IntegrationRepository,
    IntegrationUpdateFailed
)
from cache import CacheService, get_cache_service
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.integration_service.prepared_integration_update_request import PreparedIntegrationUpdateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/update-integration', status_code=status.HTTP_204_NO_CONTENT)
async def update_integration(
    payload: PreparedIntegrationUpdateRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> None:
    user_identity = get_current_identity()
    integration_repo = IntegrationRepository(connector)
    try:
        await integration_repo.update_integration(
            integration_id=payload.integration_id,
            user_id=payload.user_id,
            organization_id=payload.organization_id,
            update_args=payload.update_args
        )

        await cache_service.cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )
    except IntegrationUpdateFailed as e:
        logger.error(
            f'Update integration failed with DB error {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )

    except Exception as e:
        logger.error(
            f'Unexpected update integration error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
