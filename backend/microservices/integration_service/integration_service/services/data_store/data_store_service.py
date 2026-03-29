import logging
from uuid import UUID
from typing import Callable
from svc_integration_contracts.models import IntegrationCreateRequest, IntegrationUpdateRequest
from kafka_messaging.message_bus.async_kafka_message_bus import AsyncKafkaMessageBus
from kafka_messaging.events.integration_service import IntegrationCreated
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient

from integration_service.api.context import UserIdentity
from integration_service.cache import CacheService
from integration_service.database.exceptions import (
    IntegrationCreateFailed,
    SecretsCreateFailed,
    IntegrationDeleteFailed,
    IntegrationUpdateFailed,
    KekKidGetFailed
)
from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.mappers.integration import integration_create_from_dto, integration_update_from_dto
from integration_service.domain.mappers.secret import secrets_from_dto


logger = logging.getLogger(__name__)

class DataStoreService:
    def __init__(
        self,
        repo: DataStoreRepository,
        bus: AsyncKafkaMessageBus,
        cache_service: CacheService,
        crypto_client_factory: Callable[[str], CryptoClient]
    ) -> None:
        self._repo = repo
        self._bus = bus
        self._cache_service = cache_service
        self._crypto_client_factory = crypto_client_factory

    async def create_integration(
        self,
        user_identity: UserIdentity,
        payload: IntegrationCreateRequest
    ) -> None:
        integration_id = None
        try:
            integration_create = integration_create_from_dto(payload)
            integration_id = await self._repo.create_integration(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                integration_create=integration_create
            )

            crypto_client = self._crypto_client_factory(payload.kek_kid)
            secrets = secrets_from_dto(
                organization_id=user_identity.organization_id,
                integration_id=integration_id,
                user_id=user_identity.user_id,
                payload=payload,
                crypto_client=crypto_client
            )

            await self._repo.create_secrets(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                secrets=secrets
            )

            await self._bus.publish(
                IntegrationCreated(
                    user_id=user_identity.user_id,
                    organization_id=user_identity.organization_id,
                    integration_id=integration_id,
                    integration_name=payload.connection_name,
                    integration_descr=payload.descr
                )
            )
            await self._cache_service.cache.delete_by_prefix(
                user_identity.organization_id,
                user_identity.user_id
            )
        except (IntegrationCreateFailed, SecretsCreateFailed) as e:
            logger.error(
                'Create integration failed due to database dependency.',
                extra={
                    'org_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'integration_id': str(integration_id) if integration_id else None,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            await self._compensate_delete_integration(
                user_identity=user_identity,
                integration_id=integration_id
            )
            raise

        except Exception as e:
            logger.error(
                'Unexpected error during create_integration.',
                extra={
                    'org_id': str(user_identity.organization_id),
                    'user_id': str(user_identity.user_id),
                    'integration_id': str(integration_id) if integration_id else None,
                    'error_type': type(e).__name__,
                },
                exc_info=True,
            )
            await self._compensate_delete_integration(
                user_identity=user_identity,
                integration_id=integration_id
            )
            raise

    async def update_integration(
        self,
        user_identity: UserIdentity,
        integration_id: UUID,
        payload: IntegrationUpdateRequest
    ) -> None:
        try:
            integration_update = integration_update_from_dto(payload)
            kek_kid = await self._repo.get_kek_kid(
                integration_id=integration_id,
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id
            )
            secrets = secrets_from_dto(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                integration_id=integration_id,
                crypto_client=self._crypto_client_factory(kek_kid),
                payload=payload
            )
            await self._repo.update_integration(
                integration_id=integration_id,
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_update=integration_update,
                secrets=secrets
            )
            await self._cache_service.cache.delete_by_prefix(
                user_identity.organization_id,
                user_identity.user_id,
            )
        except (IntegrationUpdateFailed, KekKidGetFailed) as e:
            logger.error(
                'Update integration failed due to database dependency.',
                extra={
                    'org_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'integration_id': str(integration_id) if integration_id else None,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                'Unexpected error during update_integration.',
                extra={
                    'org_id': str(user_identity.organization_id),
                    'user_id': str(user_identity.user_id),
                    'integration_id': str(integration_id) if integration_id else None,
                    'error_type': type(e).__name__,
                },
                exc_info=True,
            )
            raise

    async def _compensate_delete_integration(
        self,
        user_identity: UserIdentity,
        integration_id: UUID
    ) -> None:
        if not integration_id:
            return None

        try:
            await self._repo.delete_integration(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=integration_id
            )
        except IntegrationDeleteFailed:
            logger.error(
                'Compensation failed: unable to delete integration after creation failure.',
                extra={
                    'org_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'integration_id': str(integration_id)
                },
                exc_info=True
            )
