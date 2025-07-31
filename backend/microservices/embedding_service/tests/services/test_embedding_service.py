import unittest
from unittest.mock import patch, MagicMock

from services.embedding_service import Embedder, embed


class TestEmbedder(unittest.IsolatedAsyncioTestCase):
    async def test_generate_embedding_returns_expected_embedding(self):
        mock_embedding = [0.1, 0.2, 0.3]

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response

        embedder = Embedder(client=mock_client, datastream='test input')
        result = await embedder.generate_embedding()

        self.assertEqual(result, mock_embedding)
        mock_client.embeddings.create.assert_called_once_with(
            input='test input',
            model='text-embedding-3-small'
        )


class TestEmbedFunction(unittest.IsolatedAsyncioTestCase):
    @patch('services.embedding_service.load_open_ai_client')
    @patch('services.embedding_service.os.getenv')
    async def test_embed_function(self, mock_getenv, mock_load_client):
        mock_getenv.return_value = 'fake-key'

        mock_embedding = [0.5, 0.6]
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_load_client.return_value = mock_client

        result = await embed('sample text')

        self.assertEqual(result, mock_embedding)
        mock_getenv.assert_called_once()
        mock_load_client.assert_called_once_with('fake-key')
        mock_client.embeddings.create.assert_called_once_with(
            input='sample text',
            model='text-embedding-3-small'
        )


if __name__ == '__main__':
    unittest.main()
