import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from embedding_service.cache import get_cache_service
from embedding_service.api.router.embed_router import router
from embedding_service.api.models.embedding_response import EmbeddingResponse
from embedding_service.api.models.query_embedding_request import QueryEmbeddingRequest
from embedding_service.services.embedding.exceptions import MissingEmbedderEngine


class TestEmbed(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock
        }
        self.request = QueryEmbeddingRequest(
            datastream='What is oldest marvel character?'
        )
        self.embedder_instance_mock = AsyncMock()
        self.embedding = [0.1, 0.5, 0.8]
        self.embedder_instance_mock.generate_embedding.return_value = self.embedding
        self.embedder_cls_mock = MagicMock()
        self.embedder_cls_mock.return_value = self.embedder_instance_mock

    def test_returns_cached_embedding(self):
        cached = EmbeddingResponse(embedding=[0.1, 0.4, 0.8])
        self.cache_mock.get_embedding.return_value = cached

        response = self.client.post('/v1/embedding/embed', json=self.request.model_dump())
        self.assertEqual(200, response.status_code)
        self.assertEqual(cached, EmbeddingResponse(**response.json()))

    @patch('embedding_service.api.router.embed_router.dispatch_embedder')
    @patch('embedding_service.api.router.embed_router.get_current_identity')
    def test_builds_embedding_and_adds_cache(self, get_current_identity_mock, dispatch_embedder_mock):
        self.cache_mock.get_embedding.return_value = None
        dispatch_embedder_mock.return_value = self.embedder_cls_mock
        get_current_identity_mock.return_value = 'no-matter'
        response = self.client.post('/v1/embedding/embed', json=self.request.model_dump())

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json()['embedding'], self.embedding)
        dispatch_embedder_mock.assert_called_once()
        self.embedder_instance_mock.generate_embedding.assert_awaited_once_with(self.request.datastream)
        self.cache_mock.set_embedding.assert_awaited_once_with(
            user_identity='no-matter',
            request=self.request,
            response=EmbeddingResponse(embedding=self.embedding)
        )

    @patch('embedding_service.api.router.embed_router.dispatch_embedder')
    def test_raises_missing_embedder_engine(self, dispatch_embedder_mock):
        self.cache_mock.get_embedding.return_value = None
        dispatch_embedder_mock.side_effect = MissingEmbedderEngine('Embedder failed')
        response = self.client.post('/v1/embedding/embed', json=self.request.model_dump())
        self.assertEqual(424, response.status_code)
        self.assertIn('Embedder failed', response.json()['detail']['message'])

    @patch('embedding_service.api.router.embed_router.dispatch_embedder')
    def test_raises_unexpected_exception(self, dispatch_embedder_mock):
        self.cache_mock.get_embedding.return_value = None
        dispatch_embedder_mock.side_effect = RuntimeError('Something went wrong')
        response = self.client.post('/v1/embedding/embed', json=self.request.model_dump())
        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: Something went wrong', response.json()['detail']['message'])
