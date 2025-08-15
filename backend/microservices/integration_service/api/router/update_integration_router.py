from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import SQLAlchemyError


from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import (
    IntegrationRepository,
    IntegrationUpdateFailed
)
from cache import CacheService, get_cache_service
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.integration_service.prepared_integration_update_request import PreparedIntegrationUpdateRequest


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
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unhandled error: {str(e)}'
        )
