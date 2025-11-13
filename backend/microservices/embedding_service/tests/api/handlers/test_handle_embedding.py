import datetime
import unittest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

from embedding_service.api.handlers import handle_crawl_meta_embedding
from kafka_messaging.events.embedding_service import CrawlMetaEmbedded
from kafka_messaging.events.integration_service import IntegrationMetaCrawled, TableMeta


class TestHandleEmbedding(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.kafka_message_bus_mock = AsyncMock()
        self.embedder_instance_mock = AsyncMock()
        self.embedder_mock = MagicMock()
        self.embedder_mock.return_value = self.embedder_instance_mock
        self.integration_meta = IntegrationMetaCrawled(
            event_id=uuid.uuid4(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            user_id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            table_metas=[
                TableMeta(
                    integration_id=uuid.uuid4(),
                    schema_name='marvel',
                    table_name='characters',
                    column_names=['age', 'skills', 'power']
                ),
                TableMeta(
                    integration_id=uuid.uuid4(),
                    schema_name='dc',
                    table_name='villains',
                    column_names=['partner', 'crimes']
                ),
            ]
        )

    @patch('embedding_service.api.handlers.handle_embedding.dispatch_embedder')
    @patch('embedding_service.api.handlers.handle_embedding.get_kafka_message_bus')
    async def test_handles_embedding(self, get_kafka_message_bus_mock, dispatch_embedder_mock):
        get_kafka_message_bus_mock.return_value = self.kafka_message_bus_mock
        dispatch_embedder_mock.return_value = self.embedder_mock
        await handle_crawl_meta_embedding(self.integration_meta)


        get_kafka_message_bus_mock.assert_called_once()
        dispatch_embedder_mock.assert_called_once()
        self.kafka_message_bus_mock.publish.assert_awaited_once()
        published_event = self.kafka_message_bus_mock.publish.await_args.args[0]
        self.assertIsInstance(published_event, CrawlMetaEmbedded)
        self.assertEqual(published_event.user_id, self.integration_meta.user_id)
        self.assertEqual(published_event.organization_id, self.integration_meta.organization_id)
        self.assertEqual(len(published_event.orm_embedding), len(self.integration_meta.table_metas))

        first_in, first_out = self.integration_meta.table_metas[0], published_event.orm_embedding[0]
        self.assertEqual(first_in.integration_id, first_out.integration_id)
        self.assertEqual(first_in.schema_name, first_out.schema_name)
        self.assertEqual(first_in.table_name, first_out.table_name)

        second_in, second_out = self.integration_meta.table_metas[0], published_event.orm_embedding[0]
        self.assertEqual(second_in.integration_id, second_out.integration_id)
        self.assertEqual(second_in.schema_name, second_out.schema_name)
        self.assertEqual(second_in.table_name, second_out.table_name)

    @patch('embedding_service.api.handlers.handle_embedding.dispatch_embedder')
    @patch('embedding_service.api.handlers.handle_embedding.get_kafka_message_bus')
    async def test_failed_embedding_not_published(self, get_kafka_message_bus_mock, dispatch_embedder_mock):
        self.embedder_instance_mock.generate_embedding.side_effect = RuntimeError('boom')
        get_kafka_message_bus_mock.return_value = self.kafka_message_bus_mock
        dispatch_embedder_mock.return_value = self.embedder_mock
        with self.assertRaises(RuntimeError):
            await handle_crawl_meta_embedding(self.integration_meta)
            self.kafka_message_bus_mock.publish.assert_not_awaited()
