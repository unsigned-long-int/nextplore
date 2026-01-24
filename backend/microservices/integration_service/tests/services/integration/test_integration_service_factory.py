import unittest
from unittest.mock import MagicMock, AsyncMock

from integration_service.services.integration import IntegrationService
from integration_service.services.integration import get_integration_service
from integration_service.database.repositories import IntegrationRepository
from integration_service.cache import CacheService
from kafka_messaging.message_bus.async_kafka_message_bus import AsyncKafkaMessageBus
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


class TestGetIntegrationService(unittest.TestCase):

    def test_returns_integration_service_instance(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertIsInstance(result, IntegrationService)

    def test_passes_repo_to_service(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result._repo, mock_repo)

    def test_passes_bus_to_service(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result._bus, mock_bus)

    def test_passes_cache_service_to_service(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result._cache_service, mock_cache_service)

    def test_passes_crypto_client_factory_to_service(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result._crypto_client_factory, mock_crypto_client_factory)

    def test_passes_all_dependencies_to_service(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertIsInstance(result, IntegrationService)
        self.assertEqual(result._repo, mock_repo)
        self.assertEqual(result._bus, mock_bus)
        self.assertEqual(result._cache_service, mock_cache_service)
        self.assertEqual(result._crypto_client_factory, mock_crypto_client_factory)

    def test_creates_new_service_instance_each_call(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result1 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        result2 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertIsNot(result1, result2)
        self.assertIsInstance(result1, IntegrationService)
        self.assertIsInstance(result2, IntegrationService)

    def test_accepts_different_repos(self):
        mock_repo1 = MagicMock(spec=IntegrationRepository)
        mock_repo2 = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result1 = get_integration_service(
            repo=mock_repo1,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        result2 = get_integration_service(
            repo=mock_repo2,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result1._repo, mock_repo1)
        self.assertEqual(result2._repo, mock_repo2)

    def test_accepts_different_buses(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus1 = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_bus2 = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result1 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus1,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        result2 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus2,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result1._bus, mock_bus1)
        self.assertEqual(result2._bus, mock_bus2)

    def test_accepts_different_cache_services(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service1 = MagicMock(spec=CacheService)
        mock_cache_service2 = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result1 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service1,
            crypto_client_factory=mock_crypto_client_factory
        )

        result2 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service2,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertEqual(result1._cache_service, mock_cache_service1)
        self.assertEqual(result2._cache_service, mock_cache_service2)

    def test_accepts_different_crypto_client_factories(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory1 = MagicMock()
        mock_crypto_client_factory2 = MagicMock()

        result1 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory1
        )

        result2 = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory2
        )

        self.assertEqual(result1._crypto_client_factory, mock_crypto_client_factory1)
        self.assertEqual(result2._crypto_client_factory, mock_crypto_client_factory2)

    def test_crypto_client_factory_is_callable(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)

        mock_crypto_client = MagicMock(spec=CryptoClient)
        mock_crypto_client_factory = MagicMock(return_value=mock_crypto_client)

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        crypto_client = result._crypto_client_factory('test-kek-kid')

        self.assertEqual(crypto_client, mock_crypto_client)
        mock_crypto_client_factory.assert_called_once_with('test-kek-kid')

    def test_service_has_all_required_attributes(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertTrue(hasattr(result, '_repo'))
        self.assertTrue(hasattr(result, '_bus'))
        self.assertTrue(hasattr(result, '_cache_service'))
        self.assertTrue(hasattr(result, '_crypto_client_factory'))

    def test_service_has_create_integration_method(self):
        mock_repo = MagicMock(spec=IntegrationRepository)
        mock_bus = AsyncMock(spec=AsyncKafkaMessageBus)
        mock_cache_service = MagicMock(spec=CacheService)
        mock_crypto_client_factory = MagicMock()

        result = get_integration_service(
            repo=mock_repo,
            bus=mock_bus,
            cache_service=mock_cache_service,
            crypto_client_factory=mock_crypto_client_factory
        )

        self.assertTrue(hasattr(result, 'create_integration'))
        self.assertTrue(callable(result.create_integration))
