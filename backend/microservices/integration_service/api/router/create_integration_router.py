import logging
from fastapi import APIRouter, HTTPException, status, Depends

from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import IntegrationRepository
from database.exceptions import IntegrationCreateFailed
from utils.encryption import encrypt_integration, DecryptedIntegration
from cache import CacheService, get_cache_service
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationCreated
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.integration_service.prepared_integration_create_request import PreparedIntegrationCreateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/create-integration', status_code=status.HTTP_204_NO_CONTENT)
async def create_integration(
    payload: PreparedIntegrationCreateRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> None:
    user_identity = get_current_identity()
    integration_repo = IntegrationRepository(connector)

    decrypted_integration = DecryptedIntegration(
        **payload.model_dump()
    )
    try:
        encrypted_integration = encrypt_integration(decrypted_integration)
        integration_id = await integration_repo.create_integration(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            encrypted_integration=encrypted_integration
        )
        await get_kafka_message_bus().publish(
            IntegrationCreated(
                user_id=encrypted_integration.user_id,
                organization_id=encrypted_integration.organization_id,
                integration_id=integration_id
            )
        )

        await cache_service.cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )
    except IntegrationCreateFailed as e:
        logger.error(
            f'Create integration failed with DB error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected create integration error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
    