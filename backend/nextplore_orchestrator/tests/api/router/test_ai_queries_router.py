import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.cache import (
    get_orchestrator_cache_service,
    get_semantic_cache_service,
)
from nextplore_orchestrator.api.dependencies.llm_orchestrator import (
    get_llm_orchestrator_factory,
)
from nextplore_orchestrator.api.dependencies.microservices import (
    get_embedding_client,
    get_integration_client,
)
from nextplore_orchestrator.api.models.ai_query_request import (
    AIQueryRequest,
    QueryMode,
)
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.api.router.ai_queries_router import router
from nextplore_orchestrator.clients.embedding import EmbeddingResponseRemoteError
from nextplore_orchestrator.clients.integration import DataStoreGetRemoteError
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError
from nextplore_orchestrator.clients.vector import VectorSearchDBRemoteError
from nextplore_orchestrator.services.query_orchestrator.exceptions import (
    LlmOrchestratorBootstrapError,
    QueryRunError,
)

MODULE = "nextplore_orchestrator.api.router.ai_queries_router"


def make_request(**overrides) -> AIQueryRequest:
    payload = {
        "provider": "openai",
        "model_id": "gpt-4o",
        "prompt": "how many orders last month?",
        "is_user_model": False,
        "model_ref_id": None,
        "mode": QueryMode.EXPANDED,
        "bypass_cache": False,
    }
    payload.update(overrides)
    return AIQueryRequest(**payload)


class TestAiQuery(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.user_identity = UserIdentity(organization_id=uuid4(), user_id=uuid4())

        self.embedding_client_mock = AsyncMock()
        self.embedding_client_mock.embed.return_value = MagicMock(embedding=[0.1, 0.2])

        self.integration_client_mock = AsyncMock()

        self.cache_mock = AsyncMock()
        self.cache_mock.get_ai_query_response.return_value = None

        self.semantic_cache_mock = AsyncMock()
        self.semantic_cache_mock.lookup_semantic_cache.return_value = None

        self.llm_orchestrator_mock = AsyncMock()
        self.llm_orchestrator_mock.run.return_value = self.make_response()

        self.llm_orchestrator_factory_mock = MagicMock()
        self.llm_orchestrator_factory_mock.get_llm_orchestrator.return_value = (
            self.llm_orchestrator_mock
        )

        self.app.dependency_overrides = {
            get_active_user: lambda: self.user_identity,
            get_llm_orchestrator_factory: lambda: self.llm_orchestrator_factory_mock,
            get_embedding_client: lambda: self.embedding_client_mock,
            get_integration_client: lambda: self.integration_client_mock,
            get_orchestrator_cache_service: lambda: self.cache_mock,
            get_semantic_cache_service: lambda: self.semantic_cache_mock,
        }

    @staticmethod
    def make_response(**overrides) -> dict:
        payload = {"sql": "SELECT 1", "data": [], "cache_hit": False}
        payload.update(overrides)
        return payload

    def post(self, request: AIQueryRequest):
        return self.client.post(
            "/v1/nextplore-orchestrator/llm-inference/query",
            json=request.model_dump(mode="json"),
        )


class TestExactCacheHit(TestAiQuery):
    def test_returns_the_cached_response(self):
        self.cache_mock.get_ai_query_response.return_value = AIQueryResponse(
            **self.make_response(sql="SELECT cached")
        )

        response = self.post(make_request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sql"], "SELECT cached")

    def test_marks_the_response_as_a_cache_hit(self):
        self.cache_mock.get_ai_query_response.return_value = AIQueryResponse(
            **self.make_response()
        )

        response = self.post(make_request())

        self.assertTrue(response.json()["cache_hit"])

    def test_does_not_call_the_llm_on_a_cache_hit(self):
        self.cache_mock.get_ai_query_response.return_value = AIQueryResponse(
            **self.make_response()
        )

        self.post(make_request())

        self.llm_orchestrator_mock.run.assert_not_awaited()

    def test_skipped_entirely_when_bypass_cache_is_set(self):
        self.cache_mock.get_ai_query_response.return_value = AIQueryResponse(
            **self.make_response(sql="SELECT should_not_be_returned")
        )

        response = self.post(make_request(bypass_cache=True))

        self.cache_mock.get_ai_query_response.assert_not_awaited()
        self.assertNotEqual(response.json()["sql"], "SELECT should_not_be_returned")


class TestSemanticCacheHit(TestAiQuery):
    def test_returns_the_semantic_match_when_exact_cache_misses(self):
        match_mock = MagicMock()
        match_mock.json_payload = {"sql": "SELECT semantic", "data": []}
        self.semantic_cache_mock.lookup_semantic_cache.return_value = match_mock

        response = self.post(make_request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sql"], "SELECT semantic")

    def test_marks_the_response_as_a_cache_hit(self):
        match_mock = MagicMock()
        match_mock.json_payload = {"sql": "SELECT semantic", "data": []}
        self.semantic_cache_mock.lookup_semantic_cache.return_value = match_mock

        response = self.post(make_request())

        self.assertTrue(response.json()["cache_hit"])

    def test_does_not_call_the_llm_on_a_semantic_hit(self):
        match_mock = MagicMock()
        match_mock.json_payload = {"sql": "SELECT semantic", "data": []}
        self.semantic_cache_mock.lookup_semantic_cache.return_value = match_mock

        self.post(make_request())

        self.llm_orchestrator_mock.run.assert_not_awaited()

    def test_skipped_when_bypass_cache_is_set(self):
        self.post(make_request(bypass_cache=True))

        self.semantic_cache_mock.lookup_semantic_cache.assert_not_awaited()


class TestLlmPath(TestAiQuery):
    def test_returns_the_orchestrator_response_on_full_miss(self):
        self.llm_orchestrator_mock.run.return_value = self.make_response(
            sql="SELECT fresh"
        )

        response = self.post(make_request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sql"], "SELECT fresh")

    def test_selects_the_orchestrator_for_the_requested_mode(self):
        self.post(make_request(mode=QueryMode.SIMPLE))

        self.llm_orchestrator_factory_mock.get_llm_orchestrator.assert_called_once_with(
            QueryMode.SIMPLE
        )

    def test_stores_both_caches_after_a_fresh_response(self):
        self.post(make_request())

        self.cache_mock.set_ai_query_response.assert_awaited_once()
        self.semantic_cache_mock.store_semantic_cache_entry.assert_awaited_once()

    def test_does_not_store_when_bypass_cache_is_set(self):
        self.post(make_request(bypass_cache=True))

        self.cache_mock.set_ai_query_response.assert_not_awaited()
        self.semantic_cache_mock.store_semantic_cache_entry.assert_not_awaited()


@patch(f"{MODULE}.user_llm_spec_from_llm_config")
@patch(f"{MODULE}.base_llm_spec_from_query_request")
class TestUserModelPath(TestAiQuery):
    def test_fetches_the_user_llm_config_when_is_user_model_is_true(
        self, base_spec_mock, user_spec_mock
    ):
        model_ref_id = uuid4()
        base_spec_mock.return_value = MagicMock(user_llm_config=None)
        self.integration_client_mock.get_user_llm_config.return_value = MagicMock()

        self.post(make_request(is_user_model=True, model_ref_id=model_ref_id))

        self.integration_client_mock.get_user_llm_config.assert_awaited_once_with(
            organization_id=self.user_identity.organization_id,
            user_id=self.user_identity.user_id,
            model_id=model_ref_id,
        )

    def test_does_not_fetch_user_llm_config_when_is_user_model_is_false(
        self, base_spec_mock, user_spec_mock
    ):
        base_spec_mock.return_value = MagicMock(user_llm_config=None)

        self.post(make_request(is_user_model=False))

        self.integration_client_mock.get_user_llm_config.assert_not_awaited()

    def test_attaches_the_mapped_config_to_the_llm_spec(
        self, base_spec_mock, user_spec_mock
    ):
        llm_spec_mock = MagicMock(user_llm_config=None)
        base_spec_mock.return_value = llm_spec_mock
        self.integration_client_mock.get_user_llm_config.return_value = MagicMock()
        mapped_mock = MagicMock()
        user_spec_mock.return_value = mapped_mock

        self.post(make_request(is_user_model=True, model_ref_id=uuid4()))

        self.assertIs(llm_spec_mock.user_llm_config, mapped_mock)


class TestRemoteErrorHandling(TestAiQuery):
    def test_model_response_remote_error_becomes_424(self):
        self.llm_orchestrator_mock.run.side_effect = ModelResponseRemoteError("down")

        response = self.post(make_request())

        self.assertEqual(response.status_code, 424)

    def test_embedding_remote_error_becomes_424(self):
        self.embedding_client_mock.embed.side_effect = EmbeddingResponseRemoteError(
            "down"
        )

        response = self.post(make_request())

        self.assertEqual(response.status_code, 424)

    def test_datastore_get_remote_error_becomes_424(self):
        self.integration_client_mock.get_user_llm_config.side_effect = (
            DataStoreGetRemoteError("down")
        )

        with patch(f"{MODULE}.base_llm_spec_from_query_request") as base_spec_mock:
            base_spec_mock.return_value = MagicMock(user_llm_config=None)
            response = self.post(make_request(is_user_model=True, model_ref_id=uuid4()))

        self.assertEqual(response.status_code, 424)

    def test_vector_search_remote_error_becomes_424(self):
        self.semantic_cache_mock.lookup_semantic_cache.side_effect = (
            VectorSearchDBRemoteError("down")
        )

        response = self.post(make_request())

        self.assertEqual(response.status_code, 424)

    def test_remote_error_detail_includes_the_message(self):
        self.llm_orchestrator_mock.run.side_effect = ModelResponseRemoteError(
            "provider timeout"
        )

        response = self.post(make_request())

        self.assertIn("provider timeout", response.json()["detail"]["message"])


class TestLocalErrorHandling(TestAiQuery):
    def test_query_run_error_becomes_424(self):
        self.llm_orchestrator_mock.run.side_effect = QueryRunError("bad sql")

        response = self.post(make_request())

        self.assertEqual(response.status_code, 424)

    def test_bootstrap_error_becomes_424(self):
        self.llm_orchestrator_factory_mock.get_llm_orchestrator.side_effect = (
            LlmOrchestratorBootstrapError("no provider configured")
        )

        response = self.post(make_request())

        self.assertEqual(response.status_code, 424)


class TestUnexpectedErrorHandling(TestAiQuery):
    def test_unexpected_exception_becomes_500(self):
        self.llm_orchestrator_mock.run.side_effect = RuntimeError("kaboom")

        response = self.post(make_request())

        self.assertEqual(response.status_code, 500)

    def test_500_detail_includes_the_original_message(self):
        self.llm_orchestrator_mock.run.side_effect = RuntimeError("kaboom")

        response = self.post(make_request())

        self.assertIn("kaboom", response.json()["detail"]["message"])
