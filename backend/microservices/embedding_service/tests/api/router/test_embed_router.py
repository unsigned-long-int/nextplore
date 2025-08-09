import unittest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from api.router.embed_router import router
from nextplore_shared.contracts.embedding_service.embedding_response import EmbeddingResponse
from services.exceptions import EmbeddingFailed


class TestEmbeddingRouter(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url='http://test'
        )

        self.payload = {
            'datastream': 'get me marvel_characters'
        }

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.embedding_service_cache')
    async def test_returns_cached_embedding(self, mock_cache, mock_identity):
        mock_cache.get_embedding = AsyncMock(return_value=EmbeddingResponse(embedding=[0.1, 0.2, 0.3]))

        response = await self.client.post('/v1/embedding/embed', json=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'embedding': [0.1, 0.2, 0.3]})
        mock_cache.get_embedding.assert_awaited_once()
        mock_cache.set_embedding.assert_not_called()

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.handle_query_embedding', new_callable=AsyncMock)
    @patch('api.router.embed_router.embedding_service_cache')
    async def test_computes_embedding_and_sets_cache(self, mock_cache, mock_handle_embed, mock_identity):
        mock_cache.get_embedding = AsyncMock(return_value=None)
        mock_cache.set_embedding = AsyncMock()
        mock_handle_embed.return_value = EmbeddingResponse(embedding=[0.4, 0.5, 0.6])

        response = await self.client.post('/v1/embedding/embed', json=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'embedding': [0.4, 0.5, 0.6]})
        mock_cache.get_embedding.assert_awaited_once()
        mock_handle_embed.assert_awaited_once()
        mock_cache.set_embedding.assert_awaited_once()

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.handle_query_embedding', new_callable=AsyncMock)
    @patch('api.router.embed_router.embedding_service_cache')
    async def test_embedding_failed_dependency(self, mock_cache, mock_handle_embed, mock_identity):
        mock_cache.get_embedding = AsyncMock(return_value=None)
        mock_handle_embed.side_effect = EmbeddingFailed('Model crashed')

        response = await self.client.post('/v1/embedding/embed', json=self.payload)

        self.assertEqual(response.status_code, 424)
        self.assertIn('Model crashed', response.json()['detail']['message'])

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.handle_query_embedding', new_callable=AsyncMock)
    @patch('api.router.embed_router.embedding_service_cache')
    async def test_unexpected_error_returns_500(self, mock_cache, mock_handle_embed, mock_identity):
        mock_cache.get_embedding = AsyncMock(return_value=None)
        mock_handle_embed.side_effect = RuntimeError('Something exploded')

        response = await self.client.post('/v1/embedding/embed', json=self.payload)

        self.assertEqual(response.status_code, 500)
        self.assertIn('Unexpected error', response.json()['detail']['message'])

    async def asyncTearDown(self):
        await self.client.aclose()
