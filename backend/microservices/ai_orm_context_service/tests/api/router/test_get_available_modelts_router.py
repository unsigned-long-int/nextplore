import unittest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient

from api.router.get_available_models_router import router
from nextplore_shared.contracts.ai_orm_context_service.avilable_models_response import (
    ModelInfo,
    AvailableModelsResponse
)


class TestGetModels(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        mock_registry = MagicMock()
        mock_registry.list_models.return_value = [
            {
                'provider': 'openai',
                'model_id': 'gpt-3.5',
                'label': 'GPT-3.5',
                'tags': ['chat', 'nlp']
            }
        ]
        self.mock_registry = mock_registry
        self.app.state.models_registry = mock_registry

        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url='https://test'
        )


    @patch('api.router.get_available_models_router.ai_orm_context_service_cache')
    async def test_returns_cached_models(self, mock_cache):
        mock_cache.get_models = AsyncMock(return_value=AvailableModelsResponse(models=[
            ModelInfo(provider='openai', model_id='gpt-4', label='GPT-4', tags=['chat'])
        ]))

        response = await self.client.get('/v1/ai-orm/get-models')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'models': [
                {
                    'provider': 'openai',
                    'model_id': 'gpt-4',
                    'label': 'GPT-4',
                    'tags': ['chat']
                }
            ]
        })
        mock_cache.get_models.assert_awaited_once()
        mock_cache.set_models.assert_not_called()

    @patch('api.router.get_available_models_router.get_models_registry')
    @patch('api.router.get_available_models_router.ai_orm_context_service_cache')
    async def test_builds_models_and_sets_cache(self, mock_cache, mock_get_registry):
        mock_cache.get_models = AsyncMock(return_value=None)
        mock_cache.set_models = AsyncMock()

        mock_registry_instance = MagicMock()
        mock_registry_instance.list_models.return_value = [
            {
                'provider': 'openai',
                'model_id': 'gpt-3.5',
                'label': 'GPT-3.5',
                'tags': ['chat', 'nlp']
            },
            {
                'provider': 'anthropic',
                'model_id': 'claude-2',
                'label': 'Claude 2',
                'tags': ['chat']
            }
        ]
        mock_get_registry.return_value = mock_registry_instance
        self.app.state.models_registry = mock_registry_instance

        response = await self.client.get('/v1/ai-orm/get-models')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['models']), 2)
        self.assertEqual(body['models'][0]['provider'], 'openai')
        self.assertEqual(body['models'][1]['provider'], 'anthropic')

        mock_cache.get_models.assert_awaited_once()
        mock_cache.set_models.assert_awaited_once()

    async def asyncTearDown(self):
        await self.client.aclose()
