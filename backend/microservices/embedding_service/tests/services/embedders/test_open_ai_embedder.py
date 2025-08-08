import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import os

from services.embedders.open_ai_embedder import OpenAIEmbedder
from services.exceptions import EmbeddingFailed


class TestOpenAIEmbedder(unittest.IsolatedAsyncioTestCase):

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-key'})
    @patch('services.embedders.open_ai_embedder.load_open_ai_client')
    async def test_generate_embedding_success(self, mock_loader):
        fake_embedding = [0.1, 0.2, 0.3]
        mock_client = MagicMock()
        mock_client.embeddings.create = AsyncMock(return_value=MagicMock(
            data=[MagicMock(embedding=fake_embedding)]
        ))
        mock_loader.return_value = mock_client

        embedder = OpenAIEmbedder(model_name='text-embedding-3-small')

        result = await embedder.generate_embedding('get me all marvel_characters')

        self.assertEqual(result, fake_embedding)
        mock_client.embeddings.create.assert_awaited_once_with(
            input='get me all marvel_characters',
            model='text-embedding-3-small'
        )

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-key'})
    @patch('services.embedders.open_ai_embedder.load_open_ai_client')
    async def test_generate_embedding_raises_embedding_failed(self, mock_loader):
        mock_client = MagicMock()
        mock_client.embeddings.create = AsyncMock(side_effect=RuntimeError('OpenAI down'))
        mock_loader.return_value = mock_client

        embedder = OpenAIEmbedder()

        with self.assertRaises(EmbeddingFailed) as context:
            await embedder.generate_embedding('get me failures!')

        self.assertIsInstance(context.exception, EmbeddingFailed)
        mock_client.embeddings.create.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
