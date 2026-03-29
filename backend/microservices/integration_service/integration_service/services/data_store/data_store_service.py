import logging
from uuid import UUID
from typing import Callable
from svc_integration_contracts.models import DataStoreCreateRequest, DataStoreUpdateRequest
from kafka_messaging.message_bus.async_kafka_message_bus import AsyncKafkaMessageBus
from kafka_messaging.events.integration_service import DataStoreCreated
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient

from integration_service.api.context import UserIdentity
from integration_service.cache import CacheService
from integration_service.database.exceptions import (
    DataStoreCreateFailed,
    SecretsCreateFailed,
    DataStoreDeleteFailed,
    DataStoreUpdateFailed,
    KekKidGetFailed
)
from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.mappers.datastore import datastore_create_from_dto, datastore_update_from_dto
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

    async def create_datastore(
        self,
        user_identity: UserIdentity,
        payload: DataStoreCreateRequest,
    ) -> None:
        datastore_id = None
        try:
            datastore_create = datastore_create_from_dto(payload)
            datastore_id = await self._repo.create_datastore(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                datastore_create=datastore_create
            )

            crypto_client = self._crypto_client_factory(payload.kek_kid)
            secrets = secrets_from_dto(
                organization_id=user_identity.organization_id,
                datastore_id=datastore_id,
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
                DataStoreCreated(
                    user_id=user_identity.user_id,
                    organization_id=user_identity.organization_id,
                    datastore_id=datastore_id,
                    datastore_name=payload.connection_name,
                    datastore_descr=payload.descr
                )
            )
            await self._cache_service.cache.delete_by_prefix(
                user_identity.organization_id,
                user_identity.user_id
            )
        except (DataStoreCreateFailed, SecretsCreateFailed) as e:
            logger.error(
                'Create data store failed due to database dependency.',
                extra={
                    'org_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'datastore_id': str(datastore_id) if datastore_id else None,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            await self._compensate_delete_datastore(
                user_identity=user_identity,
                datastore_id=datastore_id
            )
            raise

        except Exception as e:
            logger.error(
                'Unexpected error during create_integration.',
                extra={
                    'org_id': str(user_identity.organization_id),
                    'user_id': str(user_identity.user_id),
                    'datastore_id': str(datastore_id) if datastore_id else None,
                    'error_type': type(e).__name__,
                },
                exc_info=True,
            )
            await self._compensate_delete_datastore(
                user_identity=user_identity,
                datastore_id=datastore_id
            )
            raise

    async def update_datastore(
        self,
        user_identity: UserIdentity,
        datastore_id: UUID,
        payload: DataStoreUpdateRequest
    ) -> None:
        try:
            datastore_update = datastore_update_from_dto(payload)
            kek_kid = await self._repo.get_kek_kid(
                datastore_id=datastore_id,
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id
            )
            secrets = secrets_from_dto(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                datastore_id=datastore_id,
                crypto_client=self._crypto_client_factory(kek_kid),
                payload=payload
            )
            await self._repo.update_datastore(
                datastore_id=datastore_id,
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                datastore_update=datastore_update,
                secrets=secrets
            )
            await self._cache_service.cache.delete_by_prefix(
                user_identity.organization_id,
                user_identity.user_id,
            )
        except (DataStoreUpdateFailed, KekKidGetFailed) as e:
            logger.error(
                'Update data store failed due to database dependency.',
                extra={
                    'org_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'datastore_id': str(datastore_id) if datastore_id else None,
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
                    'datastore_id': str(datastore_id) if datastore_id else None,
                    'error_type': type(e).__name__,
                },
                exc_info=True,
            )
            raise

    async def _compensate_delete_datastore(
        self,
        user_identity: UserIdentity,
        datastore_id: UUID
    ) -> None:
        if not datastore_id:
            return None

        try:
            await self._repo.delete_datastore(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                datastore_id=datastore_id
            )
        except DataStoreDeleteFailed:
            logger.error(
                'Compensation failed: unable to delete data store after creation failure.',
                extra={
                    'org_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'datastore_id': str(datastore_id)
                },
                exc_info=True
            )
