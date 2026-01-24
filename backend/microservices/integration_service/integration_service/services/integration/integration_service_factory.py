from fastapi import Depends
from typing import Callable
from kafka_messaging.message_bus import get_kafka_message_bus
from kafka_messaging.message_bus.async_kafka_message_bus import AsyncKafkaMessageBus
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.crypto_client_factory import get_crypto_client


from integration_service.database.repositories import IntegrationRepository
from integration_service.services.integration import IntegrationService

from integration_service.api.dependencies.get_repo import get_repo
from integration_service.cache import CacheService, get_cache_service


def get_integration_service(
    repo: IntegrationRepository = Depends(get_repo),
    bus: AsyncKafkaMessageBus = Depends(get_kafka_message_bus),
    cache_service: CacheService = Depends(get_cache_service),
    crypto_client_factory: Callable[[str], CryptoClient] = Depends(get_crypto_client)
) -> IntegrationService:
    return IntegrationService(
        repo=repo,
        bus=bus,
        cache_service=cache_service,
        crypto_client_factory=crypto_client_factory
    )
