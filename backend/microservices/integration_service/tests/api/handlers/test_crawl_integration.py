import unittest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock, ANY

from integration_service.api.handlers import (
    crawl_initial_datastore_metadata,
    crawl_filtered_datastore_metadata,
)


MODULE = 'integration_service.api.handlers.crawl_datastore'


def make_event(**overrides):
    event = MagicMock()
    event.user_id = uuid.uuid4()
    event.organization_id = uuid.uuid4()
    event.datastore_id = uuid.uuid4()
    event.datastore_name = 'test-data_store'
    event.datastore_descr = 'test description'
    for k, v in overrides.items():
        setattr(event, k, v)
    return event


def make_table_meta(**overrides):
    defaults = {
        'datastore_id': uuid.uuid4(),
        'schema_name': 'public',
        'table_name': 'sales',
        'column_names': ['id', 'amount'],
    }
    return {**defaults, **overrides}


def make_filtered_request(**overrides):
    request = MagicMock()
    request.datastores = ['int-789']
    request.schemas = ['public']
    request.tables = ['sales']
    for k, v in overrides.items():
        setattr(request, k, v)
    return request


class TestCrawlInitialIntegrationMetadata(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.event = make_event()
        self.repo = MagicMock()
        self.engine_manager = MagicMock()

    @patch(f'{MODULE}.get_kafka_message_bus')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_calls_build_catalog_with_always_true_specs(
        self,
        mock_build_catalog,
        mock_get_bus,
    ):
        mock_build_catalog.return_value = MagicMock(table_metas=[])
        mock_get_bus.return_value = AsyncMock()

        await crawl_initial_datastore_metadata(
            self.event, self.repo, self.engine_manager
        )

        mock_build_catalog.assert_awaited_once_with(
            repo=self.repo,
            engine_manager=self.engine_manager,
            user_id=self.event.user_id,
            organization_id=self.event.organization_id,
            datastore_ids=[self.event.datastore_id],
            datastore_spec=ANY,
            schema_spec=ANY,
            table_spec=ANY,
        )

    @patch(f'{MODULE}.get_kafka_message_bus')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_publishes_datastore_meta_crawled(
        self,
        mock_build_catalog,
        mock_get_bus,
    ):
        table_meta = make_table_meta()
        registry = MagicMock()
        registry.table_metas = [table_meta]
        mock_build_catalog.return_value = registry

        mock_bus = AsyncMock()
        mock_get_bus.return_value = mock_bus

        await crawl_initial_datastore_metadata(
            self.event, self.repo, self.engine_manager
        )

        mock_bus.publish.assert_awaited_once()
        published_event = mock_bus.publish.call_args.args[0]
        self.assertEqual(published_event.user_id, self.event.user_id)
        self.assertEqual(published_event.organization_id, self.event.organization_id)

    @patch(f'{MODULE}.get_kafka_message_bus')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_maps_table_metas_correctly(
        self,
        mock_build_catalog,
        mock_get_bus,
    ):
        table_meta = make_table_meta()
        registry = MagicMock()
        registry.table_metas = [table_meta]
        mock_build_catalog.return_value = registry

        mock_bus = AsyncMock()
        mock_get_bus.return_value = mock_bus

        await crawl_initial_datastore_metadata(
            self.event, self.repo, self.engine_manager
        )

        published_event = mock_bus.publish.call_args.args[0]
        self.assertEqual(len(published_event.table_metas), 1)
        mapped = published_event.table_metas[0]
        self.assertEqual(mapped.datastore_id, table_meta['datastore_id'])
        self.assertEqual(mapped.datastore_name, self.event.datastore_name)
        self.assertEqual(mapped.datastore_descr, self.event.datastore_descr)
        self.assertEqual(mapped.schema_name, table_meta['schema_name'])
        self.assertEqual(mapped.table_name, table_meta['table_name'])
        self.assertEqual(mapped.column_names, table_meta['column_names'])

    @patch(f'{MODULE}.get_kafka_message_bus')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_publishes_once_per_call(
        self,
        mock_build_catalog,
        mock_get_bus,
    ):
        registry = MagicMock()
        registry.table_metas = [make_table_meta(), make_table_meta()]
        mock_build_catalog.return_value = registry
        mock_bus = AsyncMock()
        mock_get_bus.return_value = mock_bus

        await crawl_initial_datastore_metadata(
            self.event, self.repo, self.engine_manager
        )

        self.assertEqual(mock_bus.publish.await_count, 1)

    @patch(f'{MODULE}.get_kafka_message_bus')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_does_not_publish_if_catalog_raises(
        self,
        mock_build_catalog,
        mock_get_bus,
    ):
        mock_build_catalog.side_effect = RuntimeError('catalog failed')
        mock_bus = AsyncMock()
        mock_get_bus.return_value = mock_bus

        with self.assertRaises(RuntimeError):
            await crawl_initial_datastore_metadata(
                self.event, self.repo, self.engine_manager
            )

        mock_bus.publish.assert_not_awaited()

    @patch(f'{MODULE}.get_kafka_message_bus')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_empty_table_metas_publishes_empty_list(
        self,
        mock_build_catalog,
        mock_get_bus,
    ):
        registry = MagicMock()
        registry.table_metas = []
        mock_build_catalog.return_value = registry
        mock_bus = AsyncMock()
        mock_get_bus.return_value = mock_bus

        await crawl_initial_datastore_metadata(
            self.event, self.repo, self.engine_manager
        )

        published_event = mock_bus.publish.call_args.args[0]
        self.assertEqual(published_event.table_metas, [])


class TestCrawlFilteredIntegrationMetadata(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.user_id = 'user-123'
        self.organization_id = 'org-456'
        self.request = make_filtered_request()
        self.repo = MagicMock()
        self.engine_manager = MagicMock()

    @patch(f'{MODULE}.create_specs')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_creates_specs_from_request(
        self,
        mock_build_catalog,
        mock_create_specs,
    ):
        mock_create_specs.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_build_catalog.return_value = MagicMock()

        await crawl_filtered_datastore_metadata(
            self.user_id, self.organization_id, self.request,
            self.repo, self.engine_manager
        )

        mock_create_specs.assert_called_once_with(
            datastores=self.request.datastores,
            schemas=self.request.schemas,
            tables=self.request.tables,
        )

    @patch(f'{MODULE}.create_specs')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_calls_build_catalog_with_specs(
        self,
        mock_build_catalog,
        mock_create_specs,
    ):
        datastore_spec = MagicMock()
        schema_spec = MagicMock()
        table_spec = MagicMock()
        mock_create_specs.return_value = (datastore_spec, schema_spec, table_spec)
        mock_build_catalog.return_value = MagicMock()

        await crawl_filtered_datastore_metadata(
            self.user_id, self.organization_id, self.request,
            self.repo, self.engine_manager
        )

        mock_build_catalog.assert_awaited_once_with(
            repo=self.repo,
            engine_manager=self.engine_manager,
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_ids=self.request.datastores,
            datastore_spec=ANY,
            schema_spec=ANY,
            table_spec=ANY,
        )

    @patch(f'{MODULE}.create_specs')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_returns_crawl_response_with_registry_data(
        self,
        mock_build_catalog,
        mock_create_specs,
    ):
        mock_create_specs.return_value = (MagicMock(), MagicMock(), MagicMock())
        registry = MagicMock()
        registry.datastores_enum = ['sales_db']
        registry.schemas_enum = ['public']
        registry.tables_enum = ['sales']
        registry.columns_enum = ['public.sales.id']
        registry.filter_op_enum = ['eq', 'gt']
        registry.agg_funcs_enum = ['sum', 'count']
        mock_build_catalog.return_value = registry

        from svc_integration_contracts.models import CrawlResponse
        with patch(f'{MODULE}.CrawlResponse') as mock_response:
            mock_response.return_value = MagicMock(spec=CrawlResponse)
            result = await crawl_filtered_datastore_metadata(
                self.user_id, self.organization_id, self.request,
                self.repo, self.engine_manager
            )

            mock_response.assert_called_once_with(
                datastore_registry_repr=repr(registry),
                datastores_enum=registry.datastores_enum,
                schemas_enum=registry.schemas_enum,
                tables_enum=registry.tables_enum,
                columns_enum=registry.columns_enum,
                filter_op_enum=registry.filter_op_enum,
                agg_funcs_enum=registry.agg_funcs_enum,
            )

    @patch(f'{MODULE}.create_specs')
    @patch(f'{MODULE}.build_datastores_registry_catalog', new_callable=AsyncMock)
    async def test_raises_if_catalog_fails(
        self,
        mock_build_catalog,
        mock_create_specs,
    ):
        mock_create_specs.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_build_catalog.side_effect = RuntimeError('catalog failed')

        with self.assertRaises(RuntimeError):
            await crawl_filtered_datastore_metadata(
                self.user_id, self.organization_id, self.request,
                self.repo, self.engine_manager
            )
