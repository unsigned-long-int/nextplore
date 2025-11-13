import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from integration_service.api.handlers import crawl_initial_integration_metadata
from integration_service.services.crawl.filters.logic import AlwaysTrueSpec


class TestCrawlIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.event_mock = MagicMock()
        self.backend_connector_mock = MagicMock()
        self.engine_manager_mock = MagicMock()


    @patch('integration_service.api.handlers.crawl_integration.AlwaysTrueSpec')
    @patch('integration_service.api.handlers.crawl_integration.IntegrationMetaCrawled')
    @patch('integration_service.api.handlers.crawl_integration.get_kafka_message_bus')
    @patch('integration_service.api.handlers.crawl_integration.build_integrations_registry_catalog', new_callable=AsyncMock)
    async def test_builds_and_published_integration(
        self,
        build_integrations_registry_catalog_mock,
        get_kafka_message_bus_mock,
        integration_meta_crawled_mock,
        always_truespec_mock
    ):
        integration_registry_mock = MagicMock()
        kafka_message_bus_mock = AsyncMock()
        always_true_spec = MagicMock()
        build_integrations_registry_catalog_mock.return_value = integration_registry_mock
        get_kafka_message_bus_mock.return_value = kafka_message_bus_mock
        always_truespec_mock.return_value = always_true_spec
        await crawl_initial_integration_metadata(
            self.event_mock,
            self.backend_connector_mock,
            self.engine_manager_mock
        )
        build_integrations_registry_catalog_mock.assert_awaited_once_with(
            backend_connector=self.backend_connector_mock,
            engine_manager=self.engine_manager_mock,
            user_id=self.event_mock.user_id,
            organization_id=self.event_mock.organization_id,
            integration_ids=[self.event_mock.integration_id],
            integration_spec=always_true_spec,
            schema_spec=always_true_spec,
            table_spec=always_true_spec,
        )
        integration_meta_crawled_mock.assert_called_once_with(
            user_id=self.event_mock.user_id,
            organization_id=self.event_mock.organization_id,
            table_metas=integration_registry_mock.table_metas
        )
        kafka_message_bus_mock.publish.assert_awaited_once_with(
            integration_meta_crawled_mock(
                user_id=self.event_mock.user_id,
                organization_id=self.event_mock.organization_id,
                table_metas=integration_registry_mock.table_metas
            )
        )

    @patch('integration_service.api.handlers.crawl_integration.build_integrations_registry_catalog', new_callable=AsyncMock)
    @patch('integration_service.api.handlers.crawl_integration.get_kafka_message_bus')
    async def test_does_not_publish_if_fails(
        self,
        get_kafka_message_bus_mock,
        build_integrations_registry_catalog_mock
    ):
        build_integrations_registry_catalog_mock.side_effect = RuntimeError('boom')

        with self.assertRaises(RuntimeError):
            await crawl_initial_integration_metadata(
                self.event_mock,
                self.backend_connector_mock,
                self.engine_manager_mock
            )
            get_kafka_message_bus_mock.assert_not_called()
