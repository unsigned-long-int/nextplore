import unittest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, call

from lifecycle.lifecycle import handle_crawl_meta_embedding
from api.handlers.handle_embedding import handle_query_embedding
from nextplore_shared.contracts.embedding_service.query_embedding_request import QueryEmbeddingRequest
from nextplore_shared.contracts.embedding_service.embedding_response import EmbeddingResponse
from messaging.events.integration_service import IntegrationMetaCrawled, TableMeta
from messaging.events.embedding_service import CrawlMetaEmbedded


class TestLifecycleHandlers(unittest.IsolatedAsyncioTestCase):

    @patch('api.handlers.handle_embedding.embed', new_callable=AsyncMock)
    async def test_handle_query_embedding(self, mock_embed):
        mock_embed.return_value = [0.1, 0.2, 0.3]

        req = QueryEmbeddingRequest(datastream='get me all marverl caharacters')
        response = await handle_query_embedding(req)

        self.assertIsInstance(response, EmbeddingResponse)
        self.assertEqual(response.embedding, [0.1, 0.2, 0.3])
        mock_embed.assert_awaited_once_with('get me all marverl caharacters')

    @patch('api.handlers.handle_embedding.get_kafka_message_bus')
    @patch('api.handlers.handle_embedding.embed', new_callable=AsyncMock)
    async def test_handle_crawl_meta_embedding(self, mock_embed, mock_get_bus):
        mock_embed.side_effect = [[0.1, 0.2], [0.3, 0.4]]

        integration_id1 = uuid4()
        integration_id2 = uuid4()
        table_metas = [
            TableMeta(
                integration_id=integration_id1,
                schema_name='marvel',
                table_name='characters',
                column_names=['spider-man', 'iron-man']
            ),
            TableMeta(
                integration_id=integration_id2,
                schema_name='marvel',
                table_name='powers',
                column_names=['strength', 'intelligence']
            ),
        ]

        user_id = uuid4()
        org_id = uuid4()
        event = IntegrationMetaCrawled(
            user_id=user_id,
            organization_id=org_id,
            table_metas=table_metas
        )

        mock_publish = AsyncMock()
        mock_bus_instance = AsyncMock()
        mock_bus_instance.publish = mock_publish
        mock_get_bus.return_value = mock_bus_instance

        await handle_crawl_meta_embedding(event)

        expected_calls = [call(repr(meta)) for meta in table_metas]
        mock_embed.assert_has_awaits(expected_calls)

        mock_bus_instance.publish.assert_awaited_once()
        published_event = mock_bus_instance.publish.await_args.args[0]

        self.assertIsInstance(published_event, CrawlMetaEmbedded)
        self.assertEqual(published_event.user_id, user_id)
        self.assertEqual(len(published_event.orm_embedding), 2)
        self.assertEqual(
            published_event.orm_embedding[0].integration_id, integration_id1
        )
    
