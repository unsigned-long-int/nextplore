import unittest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from api.router.get_available_models_router import router
from nextplore_sdk.contracts.ai_orm_context_service.avilable_models_response import (
    ModelInfo,
    AvailableModelsResponse,
)
from cache import get_cache_service, CacheService
from services.models_registry import get_models_registry, ModelsRegistry


class TestGetModels(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.mock_cache: CacheService = MagicMock()
        self.mock_cache.get_models = AsyncMock()
        self.mock_cache.set_models = AsyncMock()

        self.mock_registry: ModelsRegistry = MagicMock()
        self.mock_registry.list_models.return_value = [
            {
                "provider": "openai",
                "model_id": "gpt-3.5",
                "label": "GPT-3.5",
                "tags": ["chat", "nlp"],
            }
        ]

        self.app.dependency_overrides[get_cache_service] = lambda: self.mock_cache
        self.app.dependency_overrides[get_models_registry] = lambda: self.mock_registry

        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="https://test",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.app.dependency_overrides.clear()

    async def test_returns_cached_models(self):
        cached = AvailableModelsResponse(
            models=[
                ModelInfo(
                    provider="openai",
                    model_id="gpt-4",
                    label="GPT-4",
                    tags=["chat"],
                )
            ]
        )
        self.mock_cache.get_models.return_value = cached

        response = await self.client.get("/v1/ai-orm/get-models")

        assert response.status_code == 200
        assert response.json() == {
            "models": [
                {
                    "provider": "openai",
                    "model_id": "gpt-4",
                    "label": "GPT-4",
                    "tags": ["chat"],
                }
            ]
        }
        self.mock_cache.get_models.assert_awaited_once()
        self.mock_cache.set_models.assert_not_called()
        self.mock_registry.list_models.assert_not_called()

    async def test_builds_models_and_sets_cache(self):
        self.mock_cache.get_models.return_value = None

        self.mock_registry.list_models.return_value = [
            {
                "provider": "openai",
                "model_id": "gpt-3.5",
                "label": "GPT-3.5",
                "tags": ["chat", "nlp"],
            },
            {
                "provider": "anthropic",
                "model_id": "claude-2",
                "label": "Claude 2",
                "tags": ["chat"],
            },
        ]

        response = await self.client.get("/v1/ai-orm/get-models")

        assert response.status_code == 200
        body = response.json()
        assert len(body["models"]) == 2
        assert body["models"][0]["provider"] == "openai"
        assert body["models"][1]["provider"] == "anthropic"

        self.mock_cache.get_models.assert_awaited_once()
        self.mock_registry.list_models.assert_called_once()
        self.mock_cache.set_models.assert_awaited_once()
        args, _ = self.mock_cache.set_models.await_args
        assert isinstance(args[0], AvailableModelsResponse)

    async def test_unexpected_exception(self):
        self.mock_cache.get_models.return_value = None
        self.mock_registry.list_models.side_effect = RuntimeError("boom")

        response = await self.client.get("/v1/ai-orm/get-models")

        assert response.status_code == 500
        assert "Unexpected error" in response.json()["detail"]["message"]
        self.mock_cache.set_models.assert_not_called()
