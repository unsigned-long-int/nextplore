import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


from api.handlers.crawl_integration import crawl_initial_integration_metadata, craw_filtered_integration_metadata

from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_shared.contracts.integration_service.filtered_crawl_request import FilteredCrawlRequest
from nextplore_shared.contracts.integration_service.crawl_response import CrawlResponse
from utils.filters.logic import AlwaysTrueSpec
from messaging.events.integration_service import IntegrationMetaCrawled, IntegrationCreated, TableMeta


class TestCrawlServices(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.user_id = uuid4()
        self.org_id = uuid4()
        self.integration_id = uuid4()

        self.connector = MagicMock(spec=DatabaseBackendConnector)

        self.fake_registry = MagicMock()
        self.fake_registry.table_metas = [
            TableMeta(
                integration_id=self.integration_id,
                schema_name='public',
                table_name='users',
                column_names=['id', 'email'],
            )
        ]
        self.fake_registry.integrations_enum = ['int_a', 'int_b']
        self.fake_registry.schemas_enum = ['public', 'analytics']
        self.fake_registry.tables_enum = ['users', 'orders']
        self.fake_registry.columns_enum = ['id', 'email']
        self.fake_registry.filter_op_enum = ['=', '!=', '>', '<']
        self.fake_registry.agg_funcs_enum = ['count', 'sum']

    @patch('api.handlers.crawl_integration.get_kafka_message_bus')
    @patch('api.handlers.crawl_integration.crawl_integration_registry', new_callable=AsyncMock)
    async def test_crawl_initial_integration_metadata_publishes_event(
        self, mock_crawl_integration_registry: AsyncMock, mock_get_bus: MagicMock
    ):
        mock_crawl_integration_registry.return_value = self.fake_registry

        bus = MagicMock()
        bus.publish = AsyncMock()
        mock_get_bus.return_value = bus

        event = IntegrationCreated(
            user_id=self.user_id,
            organization_id=self.org_id,
            integration_id=self.integration_id,
        )

        await crawl_initial_integration_metadata(event=event, connector=self.connector)

        mock_crawl_integration_registry.assert_awaited_once()
        _, kwargs = mock_crawl_integration_registry.await_args
        self.assertIs(kwargs['connector'], self.connector)
        self.assertEqual(kwargs['user_id'], self.user_id)
        self.assertEqual(kwargs['organization_id'], self.org_id)
        self.assertEqual(kwargs['integration_ids'], [self.integration_id])
        self.assertIsInstance(kwargs['integration_spec'], AlwaysTrueSpec)
        self.assertIsInstance(kwargs['schema_spec'], AlwaysTrueSpec)
        self.assertIsInstance(kwargs['table_spec'], AlwaysTrueSpec)

        bus.publish.assert_awaited_once()
        (event_arg,), _ = bus.publish.await_args
        self.assertIsInstance(event_arg, IntegrationMetaCrawled)
        self.assertEqual(event_arg.user_id, self.user_id)
        self.assertEqual(event_arg.organization_id, self.org_id)
        self.assertEqual(event_arg.table_metas, self.fake_registry.table_metas)

    @patch('api.handlers.crawl_integration.create_specs')
    @patch('api.handlers.crawl_integration.crawl_integration_registry', new_callable=AsyncMock)
    async def test_craw_filtered_integration_metadata_builds_response(
        self, mock_crawl_integration_registry: AsyncMock, mock_create_specs: MagicMock
    ):

        fake_integration_spec = object()
        fake_schema_spec = object()
        fake_table_spec = object()
        mock_create_specs.return_value = (
            fake_integration_spec,
            fake_schema_spec,
            fake_table_spec,
        )

        mock_crawl_integration_registry.return_value = self.fake_registry

        req = FilteredCrawlRequest(
            integrations=[self.integration_id],
            schemas={self.integration_id: ['public']},
            tables={self.integration_id: ['users']}
        )

        resp: CrawlResponse = await craw_filtered_integration_metadata(
            user_id=self.user_id,
            organization_id=self.org_id,
            inspection_request=req,
        )

        mock_create_specs.assert_called_once_with(
            integrations=req.integrations, schemas=req.schemas, tables=req.tables
        )

        mock_crawl_integration_registry.assert_awaited_once_with(
            user_id=self.user_id,
            organization_id=self.org_id,
            integration_ids=req.integrations,
            integration_spec=fake_integration_spec,
            schema_spec=fake_schema_spec,
            table_spec=fake_table_spec,
        )

        self.assertIsInstance(resp, CrawlResponse)
        self.assertEqual(resp.integration_registry_repr, repr(self.fake_registry))
        self.assertEqual(resp.integrations_enum, self.fake_registry.integrations_enum)
        self.assertEqual(resp.schemas_enum, self.fake_registry.schemas_enum)
        self.assertEqual(resp.tables_enum, self.fake_registry.tables_enum)
        self.assertEqual(resp.columns_enum, self.fake_registry.columns_enum)
        self.assertEqual(resp.filter_op_enum, self.fake_registry.filter_op_enum)
        self.assertEqual(resp.agg_funcs_enum, self.fake_registry.agg_funcs_enum)
