import logging
from fastapi import APIRouter, HTTPException, status, Depends

from api.context import get_current_identity
from api.dependencies import get_connector
from database.repositories import IntegrationRepository, SecretRepository
from database.exceptions import IntegrationCreateFailed
from utils.mappers import to_domain_integration, to_domain_secrets
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
    secret_repo = SecretRepository(connector)

    try:
        integration = to_domain_integration(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_create_request=payload
        )
        integration_id = await integration_repo.create_integration(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration=integration
        )

        secrets = to_domain_secrets(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=integration_id,
            integration_create_request=payload
        )
        await secret_repo.create_secrets(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=integration_id,
            secrets=secrets
        )

        await get_kafka_message_bus().publish(
            IntegrationCreated(
                user_id=integration.user_id,
                organization_id=integration.organization_id,
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
    