import logging
from uuid import UUID
from fastapi import APIRouter, status, HTTPException, Depends

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import CacheService, get_cache_service
from integration_service.database.repositories import IntegrationRepository
from integration_service.database.exceptions import IntegrationDeleteFailed
from kafka_messaging.message_bus import get_kafka_message_bus
from kafka_messaging.events.integration_service import IntegrationDeleted
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['DeleteIntegration'])


@router.delete(
    '/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_integration(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
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
    
    integration_repo = IntegrationRepository(backend_connector)

    try:
        await integration_repo.delete_integration(
            integration_id=integration_id,
            user_id=user_identity.user_id, 
            organization_id=user_identity.organization_id
        )
        await get_kafka_message_bus().publish(
            IntegrationDeleted(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=integration_id
            )
        )
        await cache_service.cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )

    except IntegrationDeleteFailed as e:
        logger.error(
            f'Delete integration failed with DB error: {e}.', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )

    except Exception as e:
        logger.error(f'Unexpected delete integration error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
