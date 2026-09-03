import unittest
from unittest.mock import AsyncMock, MagicMock

from kafka_messaging.message_bus.async_kafka_message_bus import AsyncKafkaMessageBus
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient

from integration_service.api.dependencies.get_service import (
    get_data_store_service,
    get_llm_service,
)
from integration_service.cache import CacheService
from integration_service.database.repositories import DataStoreRepository, LlmRepository
from integration_service.services.data_store import DataStoreService
from integration_service.services.llm import LlmService


def make_data_store_deps(**overrides):
    defaults = {
        "repo": MagicMock(spec=DataStoreRepository),
        "bus": AsyncMock(spec=AsyncKafkaMessageBus),
        "cache_service": MagicMock(spec=CacheService),
        "crypto_client_factory": MagicMock(return_value=MagicMock(spec=CryptoClient)),
    }
    return {**defaults, **overrides}


def make_llm_deps(**overrides):
    defaults = {
        "repo": MagicMock(spec=LlmRepository),
        "crypto_client_factory": MagicMock(return_value=MagicMock(spec=CryptoClient)),
    }
    return {**defaults, **overrides}


class TestGetDataStoreService(unittest.TestCase):
    def test_returns_data_store_service(self):
        result = get_data_store_service(**make_data_store_deps())
        self.assertIsInstance(result, DataStoreService)

    def test_passes_repo(self):
        deps = make_data_store_deps()
        result = get_data_store_service(**deps)
        self.assertIs(result._repo, deps["repo"])

    def test_passes_bus(self):
        deps = make_data_store_deps()
        result = get_data_store_service(**deps)
        self.assertIs(result._bus, deps["bus"])

    def test_passes_cache_service(self):
        deps = make_data_store_deps()
        result = get_data_store_service(**deps)
        self.assertIs(result._cache_service, deps["cache_service"])

    def test_passes_crypto_client_factory(self):
        deps = make_data_store_deps()
        result = get_data_store_service(**deps)
        self.assertIs(result._crypto_client_factory, deps["crypto_client_factory"])

    def test_creates_new_instance_each_call(self):
        deps = make_data_store_deps()
        result1 = get_data_store_service(**deps)
        result2 = get_data_store_service(**deps)
        self.assertIsNot(result1, result2)

    def test_crypto_client_factory_is_callable_with_kek_kid(self):
        mock_client = MagicMock(spec=CryptoClient)
        factory = MagicMock(return_value=mock_client)
        result = get_data_store_service(
            **make_data_store_deps(crypto_client_factory=factory)
        )

        returned = result._crypto_client_factory("test-kek-kid")

        factory.assert_called_once_with("test-kek-kid")
        self.assertIs(returned, mock_client)


class TestGetLlmService(unittest.TestCase):
    def test_returns_llm_service(self):
        result = get_llm_service(**make_llm_deps())
        self.assertIsInstance(result, LlmService)

    def test_passes_repo(self):
        deps = make_llm_deps()
        result = get_llm_service(**deps)
        self.assertIs(result._repo, deps["repo"])

    def test_passes_crypto_client_factory(self):
        deps = make_llm_deps()
        result = get_llm_service(**deps)
        self.assertIs(result._crypto_client_factory, deps["crypto_client_factory"])

    def test_creates_new_instance_each_call(self):
        deps = make_llm_deps()
        result1 = get_llm_service(**deps)
        result2 = get_llm_service(**deps)
        self.assertIsNot(result1, result2)

    def test_crypto_client_factory_is_callable_with_kek_kid(self):
        mock_client = MagicMock(spec=CryptoClient)
        factory = MagicMock(return_value=mock_client)
        result = get_llm_service(**make_llm_deps(crypto_client_factory=factory))

        returned = result._crypto_client_factory("test-kek-kid")

        factory.assert_called_once_with("test-kek-kid")
        self.assertIs(returned, mock_client)
