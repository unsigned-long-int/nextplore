import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from api.router.embed_router import router, get_cache_service
from nextplore_sdk.contracts.embedding_service.embedding_response import EmbeddingResponse
from services.exceptions import EmbeddingFailed


class TestEmbeddingRouter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.mock_cache = SimpleNamespace(
            get_embedding=AsyncMock(),
            set_embedding=AsyncMock(),
        )

        async def _override_cache_dep():
            return self.mock_cache

        self.app.dependency_overrides[get_cache_service] = _override_cache_dep

        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url='http://test',
        )

        self.payload = {'datastream': 'get me marvel_characters'}

    async def asyncTearDown(self):
        await self.client.aclose()

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    async def test_returns_cached_embedding(self, _mock_identity):
        self.mock_cache.get_embedding.return_value = EmbeddingResponse(
            embedding=[0.1, 0.2, 0.3]
        )

        resp = await self.client.post('/v1/embedding/embed', json=self.payload)

        assert resp.status_code == 200
        assert resp.json() == {'embedding': [0.1, 0.2, 0.3]}
        self.mock_cache.get_embedding.assert_awaited_once()
        self.mock_cache.set_embedding.assert_not_called()

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.handle_query_embedding', new_callable=AsyncMock)
    async def test_computes_embedding_and_sets_cache(self, mock_handle_embed, _mock_identity):
        self.mock_cache.get_embedding.return_value = None
        mock_handle_embed.return_value = EmbeddingResponse(embedding=[0.4, 0.5, 0.6])

        resp = await self.client.post('/v1/embedding/embed', json=self.payload)

        assert resp.status_code == 200
        assert resp.json() == {'embedding': [0.4, 0.5, 0.6]}
        self.mock_cache.get_embedding.assert_awaited_once()
        mock_handle_embed.assert_awaited_once()
        self.mock_cache.set_embedding.assert_awaited_once()

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.handle_query_embedding', new_callable=AsyncMock)
    async def test_embedding_failed_dependency(self, mock_handle_embed, _mock_identity):
        self.mock_cache.get_embedding.return_value = None
        mock_handle_embed.side_effect = EmbeddingFailed('Model crashed')

        resp = await self.client.post('/v1/embedding/embed', json=self.payload)

        assert resp.status_code == 424
        assert 'Model crashed' in resp.json()['detail']['message']

    @patch('api.router.embed_router.get_current_identity', return_value='user-123')
    @patch('api.router.embed_router.handle_query_embedding', new_callable=AsyncMock)
    async def test_unexpected_error_returns_500(self, mock_handle_embed, _mock_identity):
        self.mock_cache.get_embedding.return_value = None
        mock_handle_embed.side_effect = RuntimeError('Something exploded')

        resp = await self.client.post('/v1/embedding/embed', json=self.payload)

        assert resp.status_code == 500
        assert 'Unexpected error' in resp.json()['detail']['message']
