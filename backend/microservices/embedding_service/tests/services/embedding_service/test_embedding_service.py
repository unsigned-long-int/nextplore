import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.embedding_service.embedding_service import embed


class TestEmbedFunction(unittest.IsolatedAsyncioTestCase):

    @patch('services.embedding_service.embedding_service.dispatch_embedder')
    async def test_embed_calls_generate_embedding(self, mock_dispatch):
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        mock_embedder_cls = MagicMock(return_value=mock_embedder_instance)
        mock_dispatch.return_value = mock_embedder_cls

        result = await embed('get me marvel caharacters')

        mock_dispatch.assert_called_once()
        mock_embedder_cls.assert_called_once()
        mock_embedder_instance.generate_embedding.assert_awaited_once_with('get me marvel caharacters')

        self.assertEqual(result, [0.1, 0.2, 0.3])

    @patch('services.embedding_service.embedding_service.dispatch_embedder')
    async def test_embed_with_is_query_false(self, mock_dispatch):
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.generate_embedding = AsyncMock(return_value=[0.5, 0.6])
        
        mock_embedder_cls = MagicMock(return_value=mock_embedder_instance)
        mock_dispatch.return_value = mock_embedder_cls

        result = await embed('get me marvel caharacters')

        mock_embedder_instance.generate_embedding.assert_awaited_once_with('get me marvel caharacters')
        self.assertEqual(result, [0.5, 0.6])
