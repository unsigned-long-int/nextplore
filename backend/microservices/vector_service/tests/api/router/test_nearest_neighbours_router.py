import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from svc_vector_contracts.models import EmbeddingQuery, VectorSearchResult

from vector_service.api.router.nearest_neighbours_router import router
from vector_service.services.vector_store_service.exceptions import SearchVectorDBFailed
from vector_service.services.vector_store_service.models import Vector


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class TestGetNearestNeighboursEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)

        self.mock_cache_service = MagicMock()
        self.mock_vector_store_service = MagicMock()
        self.app.state.cache_service = self.mock_cache_service
        self.app.state.vector_store_service = self.mock_vector_store_service

        self.client = TestClient(self.app)

        self.organization_id = uuid4()
        self.user_id = uuid4()

        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id, user_id=self.user_id
        )

        self.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.request = EmbeddingQuery(embedding=self.embedding)

        self.vector_results = [
            VectorSearchResult(vector_id=uuid4(), score=0.95),
            VectorSearchResult(vector_id=uuid4(), score=0.87),
            VectorSearchResult(vector_id=uuid4(), score=0.75),
        ]

    def _get_endpoint_url(self, org_id=None, user_id=None):
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        return f"/v1/vector/organizations/{org_id}/users/{user_id}/nearest-neighbours"

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_success_no_cache(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[
                Vector(id=v.vector_id, score=v.score) for v in self.vector_results
            ]
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

        returned_ids = [UUID(r["vector_id"]) for r in data]
        expected_ids = [r.vector_id for r in self.vector_results]
        self.assertEqual(returned_ids, expected_ids)

        returned_scores = [r["score"] for r in data]
        expected_scores = [r.score for r in self.vector_results]
        self.assertEqual(returned_scores, expected_scores)

        self.mock_vector_store_service.search_nearest_vectors.assert_called_once_with(
            self.user_identity, self.embedding
        )
        self.mock_cache_service.set_qdrant_vectors.assert_called_once()

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_success_from_cache(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        cached_results = self.vector_results[:2]
        self.mock_cache_service.get_qdrant_vectors = AsyncMock(
            return_value=cached_results
        )
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        self.mock_cache_service.get_qdrant_vectors.assert_called_once()
        self.mock_vector_store_service.search_nearest_vectors.assert_not_called()
        self.mock_cache_service.set_qdrant_vectors.assert_not_called()

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_with_empty_results(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[]
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(data, [])

        self.mock_cache_service.set_qdrant_vectors.assert_called_once()

    @patch("vector_service.api.router.nearest_neighbours_router.logger")
    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_forbidden_wrong_organization(
        self, mock_get_identity, mock_logger
    ):
        wrong_org_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(org_id=wrong_org_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"detail": {"message": "Forbidden"}})

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn("Forbidden request", log_call[0][0])
        self.assertEqual(log_call[1]["extra"]["org_id"], wrong_org_id)

    @patch("vector_service.api.router.nearest_neighbours_router.logger")
    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_forbidden_wrong_user(
        self, mock_get_identity, mock_logger
    ):
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(user_id=wrong_user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"detail": {"message": "Forbidden"}})

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_forbidden_both_wrong(self, mock_get_identity):
        wrong_org_id = uuid4()
        wrong_user_id = uuid4()
        mock_get_identity.return_value = self.user_identity

        response = self.client.post(
            self._get_endpoint_url(org_id=wrong_org_id, user_id=wrong_user_id),
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("vector_service.api.router.nearest_neighbours_router.logger")
    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_search_failed(self, mock_get_identity, mock_logger):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)

        error_msg = "Qdrant connection timeout"
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            side_effect=SearchVectorDBFailed(error_msg)
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

        response_data = response.json()
        self.assertIn("Client error", response_data["detail"]["message"])
        self.assertIn(error_msg, response_data["detail"]["message"])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn("Get nearest vectors failed with client error", log_call[0][0])

        self.mock_cache_service.set_qdrant_vectors.assert_not_called()

    @patch("vector_service.api.router.nearest_neighbours_router.logger")
    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_unexpected_error(
        self, mock_get_identity, mock_logger
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)

        error_msg = "Unexpected network error"
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            side_effect=RuntimeError(error_msg)
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        self.assertIn("Unexpected error", response_data["detail"]["message"])
        self.assertIn(error_msg, response_data["detail"]["message"])

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn(
            "Get nearest vectors failed with unexpected error", log_call[0][0]
        )

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_cache_get_error_continues(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(
            side_effect=Exception("Redis connection error")
        )
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[
                Vector(id=v.vector_id, score=v.score) for v in self.vector_results
            ]
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_with_different_embedding_sizes(
        self, mock_get_identity
    ):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[
                Vector(id=v.vector_id, score=v.score) for v in self.vector_results
            ]
        )

        large_embedding = [0.1] * 1536
        large_request = EmbeddingQuery(embedding=large_embedding)

        response = self.client.post(
            self._get_endpoint_url(), json=large_request.model_dump(mode="json")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mock_vector_store_service.search_nearest_vectors.assert_called_once_with(
            self.user_identity, large_embedding
        )

    def test_get_nearest_neighbours_missing_request_body(self):
        response = self.client.post(self._get_endpoint_url())

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_nearest_neighbours_invalid_uuid_in_path(self):
        response = self.client.post(
            f"/v1/vector/organizations/invalid-uuid/users/{self.user_id}/nearest-neighbours",
            json=self.request.model_dump(mode="json"),
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_invalid_embedding_format(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        invalid_request = {"embedding": ["a", "b", "c"]}

        response = self.client.post(self._get_endpoint_url(), json=invalid_request)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_empty_embedding(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[]
        )

        empty_request = EmbeddingQuery(embedding=[])

        response = self.client.post(
            self._get_endpoint_url(), json=empty_request.model_dump(mode="json")
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY],
        )

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_response_content_type(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[
                Vector(id=v.vector_id, score=v.score) for v in self.vector_results
            ]
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/json", response.headers["content-type"])

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_cache_set_fails_silently(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock(
            side_effect=Exception("Redis write error")
        )
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[
                Vector(id=v.vector_id, score=v.score) for v in self.vector_results
            ]
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch("vector_service.api.router.nearest_neighbours_router.get_current_identity")
    def test_get_nearest_neighbours_results_ordered_by_score(self, mock_get_identity):
        mock_get_identity.return_value = self.user_identity

        ordered_results = [
            VectorSearchResult(vector_id=uuid4(), score=0.99),
            VectorSearchResult(vector_id=uuid4(), score=0.80),
            VectorSearchResult(vector_id=uuid4(), score=0.61),
        ]

        self.mock_cache_service.get_qdrant_vectors = AsyncMock(return_value=None)
        self.mock_cache_service.set_qdrant_vectors = AsyncMock()
        self.mock_vector_store_service.search_nearest_vectors = AsyncMock(
            return_value=[
                Vector(id=v.vector_id, score=v.score) for v in ordered_results
            ]
        )

        response = self.client.post(
            self._get_endpoint_url(), json=self.request.model_dump(mode="json")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIsInstance(data, list)
        returned_scores = [r["score"] for r in data]
        self.assertEqual(returned_scores, [0.99, 0.80, 0.61])
