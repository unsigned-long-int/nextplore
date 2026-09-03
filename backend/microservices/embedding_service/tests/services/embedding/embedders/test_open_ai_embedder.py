import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from embedding_service.services.embedding.embedders import OpenAIEmbedder
from embedding_service.services.embedding.exceptions import EmbeddingFailed


class TestOpenAIEmbedder(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with patch(
            "embedding_service.services.embedding.embedders.open_ai_embedder.load_open_ai_client"
        ) as load_open_ai_client:
            self.client_mock = AsyncMock()
            self.client_response_mock = MagicMock()
            self.embedding_mock = MagicMock()

            self.client_response_mock.data = [self.embedding_mock]
            self.client_mock.embeddings.create.return_value = self.client_response_mock
            load_open_ai_client.return_value = self.client_mock
            self.embedder = OpenAIEmbedder()

    async def test_generates_embedding(self):
        result = await self.embedder.generate_embedding(
            "What is the strongest marvel character?"
        )
        self.client_mock.embeddings.create.assert_awaited_once_with(
            input="What is the strongest marvel character?",
            model=self.embedder.model_name,
        )
        self.assertEqual(result, self.embedding_mock.embedding)

    async def test_raises_embedding_failed(self):
        self.client_mock.embeddings.create.side_effect = RuntimeError("boom")
        with self.assertRaises(EmbeddingFailed) as ctx:
            res = await self.embedder.generate_embedding(
                "What is the strongest marvel character?"
            )
        self.assertIn("boom", str(ctx.exception))
