import unittest
import uuid
from unittest.mock import patch, AsyncMock

from embedding_service.cache import CacheService
from embedding_service.api.context import UserIdentity
from embedding_service.api.models.embedding_response import EmbeddingResponse
from embedding_service.api.models.query_embedding_request import QueryEmbeddingRequest


class TestCacheService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.cache = AsyncMock()
        self.cache_service = CacheService(self.cache)
        self.organization_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    @patch('embedding_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_get_embedding(
        self,
        get_cache_key_mock
    ):
        cached = EmbeddingResponse(embedding=[0.1, 0.14, 0.9])
        request = QueryEmbeddingRequest(datastream='Who is strongest marvel character?')
        self.cache.get_one.return_value = cached
        result = await self.cache_service.get_embedding(
            user_identity= UserIdentity(organization_id=self.organization_id, user_id=self.user_id),
            request=request
        )
        self.assertEqual(cached, result)
        get_cache_key_mock.assert_called_once_with(model=request, prefix='query-embed')
        self.cache.get_one.assert_awaited_once_with(
            self.organization_id,
            self.user_id,
            'key123',
            model=EmbeddingResponse
        )

    @patch('embedding_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_set_embedding(
        self,
        get_cache_key_mock
    ):
        response = EmbeddingResponse(embedding=[0.1, 0.14, 0.9])
        request = QueryEmbeddingRequest(datastream='Who is strongest marvel character?')
        get_cache_key_mock.return_value = 'key123'
        await self.cache_service.set_embedding(
            user_identity= UserIdentity(organization_id=self.organization_id, user_id=self.user_id),
            request=request,
            response=response
        )
        get_cache_key_mock.assert_called_once_with(model=request, prefix='query-embed')
        self.cache.set_one.assert_called_once_with(
            self.organization_id,
            self.user_id,
            'key123',
            value=response
        )

    @patch('embedding_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_delete_embedding(self, get_cache_key_mock):
        request = QueryEmbeddingRequest(datastream='Who is strongest marvel character?')
        get_cache_key_mock.return_value = 'key123'
        await self.cache_service.delete_embedding(
            user_identity= UserIdentity(organization_id=self.organization_id, user_id=self.user_id),
            request=request
        )
        self.cache.delete.assert_awaited_once_with(
            self.organization_id,
            self.user_id,
            'key123',
        )
