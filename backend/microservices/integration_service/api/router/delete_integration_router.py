import logging
from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.context import get_current_identity
from api.dependencies import get_connector
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationDeleted
from database.repositories import IntegrationRepository, IntegrationDeleteFailed
from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_shared.cache.service_caches.integration_cache.cache import integration_service_cache
from nextplore_shared.contracts.integration_service.prepared_integration_delete_request import PreparedIntegrationDeleteRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/delete-integration', status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    payload: PreparedIntegrationDeleteRequest,
    connector: DatabaseBackendConnector = Depends(get_connector)
) -> JSONResponse:
    try:
        user_identity = get_current_identity()
        integration_repo = IntegrationRepository(connector)
        await integration_repo.delete_integration(
            integration_id=payload.integration_id,
            user_id=payload.user_id, 
            organization_id=payload.organization_id
        )
        await get_kafka_message_bus().publish(
            IntegrationDeleted(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=payload.integration_id
            )
        )
        await integration_service_cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )

    except IntegrationDeleteFailed as e:
        logger.error(f'delete integration error: {e}. Integration not found.', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )

    except Exception as e:
        logger.error(f'unexpected delete integration error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
