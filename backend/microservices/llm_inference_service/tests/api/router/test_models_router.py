import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_llm_inference_contracts.models import ModelInfo

from llm_inference_service.api.router.models_router import router
from llm_inference_service.services.models_gateway.models_registry import get_models_registry
from llm_inference_service.cache import get_cache_service


ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
ENDPOINT = f'/v1/llm-inference/organizations/{ORGANIZATION_ID}/users/{USER_ID}/models'


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

        self.mock_identity = MagicMock()
        self.mock_identity.organization_id = ORGANIZATION_ID
        self.mock_identity.user_id = USER_ID

        self.models = [
            ModelInfo(provider='deepseek', model_id='deepseek-12-build', label='DeepSeek', tags=[]),
            ModelInfo(provider='openai', model_id='gpt-4o', label='GPT-4o', tags=['vision']),
        ]

    @patch('llm_inference_service.api.router.models_router.get_current_identity')
    def test_returns_cached_models(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_models.return_value = self.models

        response = self.client.get(ENDPOINT)

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [item.model_dump() for item in self.models])
        self.cache_mock.get_models.assert_awaited_once_with(self.mock_identity)
        self.models_registry_mock.list_models.assert_not_called()
        self.cache_mock.set_models.assert_not_awaited()

    @patch('llm_inference_service.api.router.models_router.get_current_identity')
    def test_processes_models_and_sets_cache(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_models.return_value = None
        self.models_registry_mock.list_models.return_value = [
            item.model_dump() for item in self.models
        ]

        response = self.client.get(ENDPOINT)

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [item.model_dump() for item in self.models])
        self.models_registry_mock.list_models.assert_called_once()
        self.cache_mock.get_models.assert_awaited_once_with(self.mock_identity)
        self.cache_mock.set_models.assert_awaited_once_with(
            user_identity=self.mock_identity,
            response=self.models
        )

    @patch('llm_inference_service.api.router.models_router.get_current_identity')
    def test_forbidden_when_organization_id_mismatch(self, get_current_identity_mock):
        mismatched_identity = MagicMock()
        mismatched_identity.organization_id = uuid.uuid4()
        mismatched_identity.user_id = USER_ID
        get_current_identity_mock.return_value = mismatched_identity

        response = self.client.get(ENDPOINT)

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch('llm_inference_service.api.router.models_router.get_current_identity')
    def test_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        mismatched_identity = MagicMock()
        mismatched_identity.organization_id = ORGANIZATION_ID
        mismatched_identity.user_id = uuid.uuid4()
        get_current_identity_mock.return_value = mismatched_identity

        response = self.client.get(ENDPOINT)

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch('llm_inference_service.api.router.models_router.get_current_identity')
    def test_raises_exception_if_registry_fails(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_models.return_value = None
        self.models_registry_mock.list_models.side_effect = RuntimeError('Unexpectedly failed')

        response = self.client.get(ENDPOINT)

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpectedly failed', response.json()['detail']['message'])
        self.cache_mock.set_models.assert_not_awaited()