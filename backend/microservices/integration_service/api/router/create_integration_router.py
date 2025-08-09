import logging
from fastapi import APIRouter, HTTPException, status

from api.context import get_current_identity
from database.repositories import IntegrationRepository
from database.exceptions import IntegrationCreateFailed
from utils.encryption import encrypt_integration, DecryptedIntegration
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationCreated
from nextplore_shared.contracts.integration_service.prepared_integration_create_request import PreparedIntegrationCreateRequest
from nextplore_shared.cache.service_caches.integration_cache.cache import integration_service_cache


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/create-integration', status_code=status.HTTP_204_NO_CONTENT)
async def create_integration(payload: PreparedIntegrationCreateRequest) -> None:
    user_identity = get_current_identity()
    integration_repo = IntegrationRepository()

    decrypted_integration = DecryptedIntegration(
        **payload.model_dump()
    )
    try:
        encrypted_integration = encrypt_integration(decrypted_integration)
        integration_id = await integration_repo.create_integration(encrypted_integration)
        await get_kafka_message_bus().publish(
            IntegrationCreated(
                user_id=encrypted_integration.user_id,
                organization_id=encrypted_integration.organization_id,
                integration_id=integration_id
            )
        )

        await integration_service_cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )
    except IntegrationCreateFailed as e:
        logger.error(f'create integration error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(f'create integration error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
    