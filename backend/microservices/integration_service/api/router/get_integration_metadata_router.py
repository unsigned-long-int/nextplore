import logging
from fastapi import APIRouter, HTTPException, status, Depends

from database.repositories import IntegrationRepository
from database.exceptions import IntegrationGetFailed
from utils.encryption import decrypt_integration
from api.context import get_current_identity
from api.dependencies import get_connector
from cache import CacheService, get_cache_service
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.integration_service.integration_metadata_request import IntegrationMetadataRequest
from nextplore_sdk.contracts.integration_service.integration_connection_profile import IntegrationMetadataResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integration', response_model=IntegrationMetadataResponse)
async def get_integration(
    payload: IntegrationMetadataRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> IntegrationMetadataResponse:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_integration_metadata(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        integration_repo = IntegrationRepository(connector)
        integration_mv_orm = await integration_repo.get_integration_secret_mv(
            user_id=payload.user_id,
            organization_id=payload.organization_id,
            integration_id=payload.integration_id
        )
        response = IntegrationMetadataResponse(
            auth=integration_mv_orm.auth,
            cloud=integration_mv_orm.cloud,
            db=integration_mv_orm.db,
            database_name=integration_mv_orm.database_name,
            port=integration_mv_orm.port,
            warehouse=integration_mv_orm.warehouse,
            username=



            auth=integration_orm.auth,
            cloud=integration_orm.cloud,
            db=integration_orm.db,
            connection_name=integration_orm.connection_name,
            host=integration_orm.host,
            database_name=integration_orm.database_name,
            autosync_on=integration_orm.autosync_on,
            warehouse=integration_orm.warehouse,
            port=integration_orm.port
        )

        await cache_service.set_integration_metadata(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except IntegrationGetFailed as e:
        logger.error(
            f'Database integration single get request failed with DB error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(f'Unexpected single get integration request error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
 