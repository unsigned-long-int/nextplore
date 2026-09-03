import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from vector_service.api.dependencies import get_vector_store_service
from vector_service.api.router.semantic_cache_lookup_router import router
from vector_service.services.vector_store_service.exceptions import SearchVectorDBFailed


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class MockSemanticMatch:
    def __init__(self, json_payload):
        self.json_payload = json_payload


class TestLookupSemanticCacheEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.mock_vector_store_service = AsyncMock()
        self.app.dependency_overrides = {
            get_vector_store_service: lambda: self.mock_vector_store_service,
        }

        self.client = TestClient(self.app)

        self.organization_id = uuid4()
        self.user_id = uuid4()

        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

        self.embedding = [0.1] * 1536
        self.json_payload = {
            "sql": "SELECT * FROM users",
            "data": [],
            "cache_hit": False,
        }

        self.valid_payload = {
            "embedding": self.embedding,
            "provider": "openai",
            "model_id": "gpt-4o",
            "model_ref_id": None,
        }

    def _get_endpoint_url(self, org_id=None, user_id=None):
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        return (
            f"/v1/vector/organizations/{org_id}/users/{user_id}/semantic-cache/lookup"
        )

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.refine_filters_from_dto"
    )
    def test_lookup_cache_hit(self, mock_refine_filters, mock_get_identity):
        mock_get_identity.return_value = self.user_identity
        mock_refine_filters.return_value = []

        self.mock_vector_store_service.lookup_semantic_cache = AsyncMock(
            return_value=MockSemanticMatch(json_payload=self.json_payload)
        )

        response = self.client.post(self._get_endpoint_url(), json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["hit"])
        self.assertEqual(data["json_payload"], self.json_payload)

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.refine_filters_from_dto"
    )
    def test_lookup_cache_miss(self, mock_refine_filters, mock_get_identity):
        mock_get_identity.return_value = self.user_identity
        mock_refine_filters.return_value = []

        self.mock_vector_store_service.lookup_semantic_cache = AsyncMock(
            return_value=None
        )

        response = self.client.post(self._get_endpoint_url(), json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertFalse(data["hit"])
        self.assertIsNone(data.get("json_payload"))

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    def test_lookup_forbidden_wrong_organization(self, mock_get_identity):
        wrong_org_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(org_id=wrong_org_id),
            json=self.valid_payload,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"detail": {"message": "Forbidden"}})

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    def test_lookup_forbidden_wrong_user(self, mock_get_identity):
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(user_id=wrong_user_id),
            json=self.valid_payload,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"detail": {"message": "Forbidden"}})

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    def test_lookup_forbidden_both_wrong(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(org_id=uuid4(), user_id=uuid4()),
            json=self.valid_payload,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("vector_service.api.router.semantic_cache_lookup_router.logger")
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    def test_lookup_forbidden_logs_error(self, mock_get_identity, mock_logger):
        wrong_org_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        self.client.post(
            self._get_endpoint_url(org_id=wrong_org_id),
            json=self.valid_payload,
        )

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn("Forbidden request", log_call[0][0])
        self.assertEqual(log_call[1]["extra"]["org_id"], wrong_org_id)

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.refine_filters_from_dto"
    )
    def test_lookup_search_vector_db_failed(
        self, mock_refine_filters, mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity
        mock_refine_filters.return_value = []

        error_msg = "Qdrant connection timeout"
        self.mock_vector_store_service.lookup_semantic_cache = AsyncMock(
            side_effect=SearchVectorDBFailed(error_msg)
        )

        response = self.client.post(self._get_endpoint_url(), json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertIn("Client error", response.json()["detail"]["message"])
        self.assertIn(error_msg, response.json()["detail"]["message"])

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.refine_filters_from_dto"
    )
    def test_lookup_unexpected_error(self, mock_refine_filters, mock_get_identity):
        mock_get_identity.return_value = self.user_identity
        mock_refine_filters.return_value = []

        error_msg = "Unexpected failure"
        self.mock_vector_store_service.lookup_semantic_cache = AsyncMock(
            side_effect=RuntimeError(error_msg)
        )

        response = self.client.post(self._get_endpoint_url(), json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Unexpected error", response.json()["detail"]["message"])
        self.assertIn(error_msg, response.json()["detail"]["message"])

    def test_lookup_invalid_uuid_organization(self):
        response = self.client.post(
            f"/v1/vector/organizations/invalid-uuid/users/{self.user_id}/semantic-cache/lookup",
            json=self.valid_payload,
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_lookup_invalid_uuid_user(self):
        response = self.client.post(
            f"/v1/vector/organizations/{self.organization_id}/users/invalid-uuid/semantic-cache/lookup",
            json=self.valid_payload,
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_lookup_missing_embedding(self):
        response = self.client.post(
            self._get_endpoint_url(),
            json={"provider": "openai", "model_id": "gpt-4o"},
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.refine_filters_from_dto"
    )
    def test_lookup_calls_refine_filters_with_payload(
        self, mock_refine_filters, mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity
        mock_refine_filters.return_value = []
        self.mock_vector_store_service.lookup_semantic_cache = AsyncMock(
            return_value=None
        )

        self.client.post(self._get_endpoint_url(), json=self.valid_payload)

        mock_refine_filters.assert_called_once()

    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.get_current_identity"
    )
    @patch(
        "vector_service.api.router.semantic_cache_lookup_router.refine_filters_from_dto"
    )
    def test_lookup_passes_embedding_to_service(
        self, mock_refine_filters, mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity
        mock_refine_filters.return_value = []
        self.mock_vector_store_service.lookup_semantic_cache = AsyncMock(
            return_value=None
        )

        self.client.post(self._get_endpoint_url(), json=self.valid_payload)

        call_kwargs = self.mock_vector_store_service.lookup_semantic_cache.call_args[1]
        self.assertEqual(call_kwargs["embedding"], self.embedding)
        self.assertEqual(call_kwargs["user_identity"], self.user_identity)
