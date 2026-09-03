import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_llm_inference_contracts.models import PromptRequest, PromptResponse

from llm_inference_service.api.router.chat_router import router
from llm_inference_service.cache import get_cache_service
from llm_inference_service.services.models_gateway.exceptions import (
    InferenceProviderMissing,
)
from llm_inference_service.services.models_gateway.models_registry import (
    get_models_registry,
)

ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
ENDPOINT = f"/v1/llm-inference/organizations/{ORGANIZATION_ID}/users/{USER_ID}/chat"


class TestGetPromptResponse(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.cache_mock = AsyncMock()
        self.models_registry_mock = MagicMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_models_registry: lambda: self.models_registry_mock,
        }

        self.mock_identity = MagicMock()
        self.mock_identity.organization_id = ORGANIZATION_ID
        self.mock_identity.user_id = USER_ID

        self.mock_model_meta = MagicMock()
        self.models_registry_mock.get_default_model_config.return_value = (
            self.mock_model_meta,
            "openai",
        )

        self.mock_provider = MagicMock()
        self.mock_provider.prompt_model = AsyncMock(return_value="Test response")

        self.mock_provider_factory = MagicMock()
        self.mock_provider_factory.create.return_value = self.mock_provider

        self.cache_mock.get_prompt_response = AsyncMock(return_value=None)
        self.cache_mock.set_prompt_response = AsyncMock()

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_returns_200_with_prompt_response(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.prompt_model = AsyncMock(
            return_value="Live long and prosper"
        )

        response = self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json()["response"], "Live long and prosper")

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_returns_cached_response_when_available(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.cache_mock.get_prompt_response = AsyncMock(
            return_value=PromptResponse(response="Cached answer")
        )

        response = self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json()["response"], "Cached answer")

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_does_not_call_provider_on_cache_hit(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.cache_mock.get_prompt_response = AsyncMock(
            return_value=PromptResponse(response="Cached")
        )

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.mock_provider.prompt_model.assert_not_called()

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_stores_response_in_cache_on_cache_miss(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.cache_mock.set_prompt_response.assert_awaited_once()

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_calls_provider_with_correct_prompt(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json={"prompt": "What is warp drive?"})

        self.mock_provider.prompt_model.assert_awaited_once_with("What is warp drive?")

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_dispatches_correct_provider(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        mock_dispatch.assert_called_once()

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_cache_lookup_uses_correct_identity_and_payload(
        self, mock_identity, mock_dispatch
    ):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json={"prompt": "Tell me about Vulcans"})

        self.cache_mock.get_prompt_response.assert_awaited_once_with(
            user_identity=self.mock_identity,
            request=PromptRequest(prompt="Tell me about Vulcans"),
        )

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_cache_set_uses_correct_identity_and_response(
        self, mock_identity, mock_dispatch
    ):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.prompt_model = AsyncMock(return_value="Vulcans are logical")

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.cache_mock.set_prompt_response.assert_awaited_once_with(
            user_identity=self.mock_identity,
            request=PromptRequest(prompt="Hello"),
            response=PromptResponse(response="Vulcans are logical"),
        )

    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_forbidden_when_organization_id_mismatch(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = uuid.uuid4()
        mismatched.user_id = USER_ID
        mock_identity.return_value = mismatched

        response = self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.assertEqual(403, response.status_code)
        self.assertIn("Forbidden", response.json()["detail"]["message"])

    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_forbidden_when_user_id_mismatch(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = ORGANIZATION_ID
        mismatched.user_id = uuid.uuid4()
        mock_identity.return_value = mismatched

        response = self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.assertEqual(403, response.status_code)
        self.assertIn("Forbidden", response.json()["detail"]["message"])

    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_does_not_call_cache_on_forbidden(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = uuid.uuid4()
        mismatched.user_id = uuid.uuid4()
        mock_identity.return_value = mismatched

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.cache_mock.get_prompt_response.assert_not_awaited()

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_returns_424_when_inference_provider_missing(
        self, mock_identity, mock_dispatch
    ):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.prompt_model = AsyncMock(
            side_effect=InferenceProviderMissing("openai provider not configured")
        )

        response = self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "openai provider not configured", response.json()["detail"]["message"]
        )

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_returns_500_on_unexpected_exception(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.prompt_model = AsyncMock(
            side_effect=RuntimeError("something exploded")
        )

        response = self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.assertEqual(500, response.status_code)
        self.assertIn("something exploded", response.json()["detail"]["message"])

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_does_not_cache_on_provider_error(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.prompt_model = AsyncMock(
            side_effect=InferenceProviderMissing("missing")
        )

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.cache_mock.set_prompt_response.assert_not_awaited()

    @patch("llm_inference_service.api.router.chat_router.dispatch_provider_factory")
    @patch("llm_inference_service.api.router.chat_router.get_current_identity")
    def test_does_not_cache_on_unexpected_error(self, mock_identity, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.prompt_model = AsyncMock(side_effect=RuntimeError("boom"))

        self.client.post(ENDPOINT, json={"prompt": "Hello"})

        self.cache_mock.set_prompt_response.assert_not_awaited()
