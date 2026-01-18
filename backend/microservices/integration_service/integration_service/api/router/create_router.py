import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from svc_integration_contracts.models import IntegrationCreateRequest
from kafka_messaging.message_bus import get_kafka_message_bus
from kafka_messaging.events.integration_service import IntegrationCreated
from nextplore_sdk.encryptor.client.azure_crypto_client import AzureCryptoClient
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.database.repositories import IntegrationRepository
from integration_service.database.exceptions import IntegrationCreateFailed, SecretsCreateFailed
from integration_service.domain.mappers.integration import integration_create_from_dto
from integration_service.domain.mappers.secret import secrets_from_dto
from integration_service.cache import CacheService, get_cache_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CreateIntegration'])


@router.post(
    '/organizations/{organization_id}/users/{user_id}/integrations',
    status_code=status.HTTP_204_NO_CONTENT
)
async def create_integration(
    organization_id: UUID,
    user_id: UUID,
    payload: IntegrationCreateRequest,
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
        integration_create = integration_create_from_dto(payload)
        integration_id = await integration_repo.create_integration(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_create=integration_create
        )
        crypto_client = AzureCryptoClient(payload.kek_kid)
        secrets = secrets_from_dto(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=integration_id,
            payload=payload,
            crypto_client=crypto_client
        )
        await integration_repo.create_secrets(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            secrets=secrets
        )

        await get_kafka_message_bus().publish(
            IntegrationCreated(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=integration_id
            )
        )
        await cache_service.cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )
    except IntegrationCreateFailed as e:
        logger.error(
            f'Create integration failed with DB error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except SecretsCreateFailed as e:
        logger.error(
            f'Create secrets failed with DB error: {e}',
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
    