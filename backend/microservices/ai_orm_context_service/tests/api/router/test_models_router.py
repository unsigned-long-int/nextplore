import unittest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_ai_orm_context_contracts.models import ModelInfo

from ai_orm_context_service.api.router.models_router import router
from ai_orm_context_service.services.orm_context.models_registry import get_models_registry
from ai_orm_context_service.cache import get_cache_service


class TestGetModels(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.models_registry_mock = MagicMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_models_registry: lambda: self.models_registry_mock,
        }

    def test_returns_cached_models(self):
        cached = [
            ModelInfo(
                provider='deepseek',
                model_id='deepseek-12-build',
                label='DeepSeek',
                tags=[]
            )
        ]

        self.cache_mock.get_models.return_value = cached

        response = self.client.get('/v1/ai-orm/models')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [item.model_dump() for item in cached])
        self.cache_mock.get_models.assert_awaited_once()
        self.models_registry_mock.list_models.assert_not_called()

    def test_processes_models_and_sets_cache(self):
        models = [
            ModelInfo(
                provider='deepseek',
                model_id='deepseek-12-build',
                label='DeepSeek',
                tags=[]
            )
        ]
        self.cache_mock.get_models.return_value = None
        self.models_registry_mock.list_models.return_value = [item.model_dump() for item in models]

        response = self.client.get('/v1/ai-orm/models')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [item.model_dump() for item in models])
        self.models_registry_mock.list_models.assert_called_once()
        self.cache_mock.get_models.assert_awaited_once()
        self.cache_mock.set_models.assert_awaited_once_with(models)


    def test_raises_exceptions_if_failed(self):
        self.cache_mock.get_models.return_value = None
        self.models_registry_mock.list_models.side_effect = RuntimeError('Unexpectedly failed')

        response = self.client.get('/v1/ai-orm/models')
        self.assertEqual(500, response.status_code)
        self.cache_mock.assert_not_awaited()
        self.assertIn('Unexpectedly failed', response.json()['detail']['message'])
