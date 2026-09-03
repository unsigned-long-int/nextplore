import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_integration_contracts.models import DataStoreStatsResponse

from integration_service.api.dependencies import get_backend_connector
from integration_service.api.router.datastore_stats_router import router
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import DataStoreGetFailed


class TestStatsRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.database_backend_connector_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_backend_connector: lambda: self.database_backend_connector_mock,
        }

        self.datastore_ids = [uuid4(), uuid4(), uuid4()]
        self.stats_response = DataStoreStatsResponse(
            datastore_ids=self.datastore_ids, datastore_count=len(self.datastore_ids)
        )

    def _url(self, org_id, user_id) -> str:
        return (
            f"/v1/integration/organizations/{org_id}/users/{user_id}/datastores/stats"
        )

    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_returns_cached_stats(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cached_stats = self.stats_response
        self.cache_mock.get_datastore_stats.return_value = cached_stats

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)
        self.cache_mock.get_datastore_stats.assert_awaited_once_with(
            user_identity=user_identity_mock
        )

        response_data = response.json()
        self.assertEqual(response_data["datastore_count"], 3)
        self.assertEqual(len(response_data["datastore_ids"]), 3)

        self.cache_mock.set_datastore_stats.assert_not_awaited()

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_fetches_and_caches_stats_when_cache_miss(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = self.datastore_ids
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        self.cache_mock.get_datastore_stats.assert_awaited_once_with(
            user_identity=user_identity_mock
        )

        repo_instance.get_user_datastore_ids.assert_awaited_once_with(
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id,
        )

        self.cache_mock.set_datastore_stats.assert_awaited_once()
        cached_response = self.cache_mock.set_datastore_stats.call_args[1]["response"]
        self.assertEqual(cached_response.datastore_count, 3)
        self.assertEqual(len(cached_response.datastore_ids), 3)

        response_data = response.json()
        self.assertEqual(response_data["datastore_count"], 3)
        self.assertEqual(len(response_data["datastore_ids"]), 3)

    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_user_id = uuid4()

        response = self.client.get(
            self._url(user_identity_mock.organization_id, different_user_id)
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

        self.cache_mock.get_datastore_stats.assert_not_awaited()

    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()

        response = self.client.get(
            self._url(different_org_id, user_identity_mock.user_id)
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.json()["detail"]["message"])

        self.cache_mock.get_datastore_stats.assert_not_awaited()

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_raises_exception_when_datastore_get_failed(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.side_effect = DataStoreGetFailed(
            "Database connection timeout"
        )
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "Database error: Database connection timeout",
            response.json()["detail"]["message"],
        )

        self.cache_mock.set_datastore_stats.assert_not_awaited()

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_raises_exception_when_generic_error(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.side_effect = RuntimeError(
            "Unexpected error occurred"
        )
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(500, response.status_code)
        self.assertIn(
            "Unexpected error: Unexpected error occurred",
            response.json()["detail"]["message"],
        )

        self.cache_mock.set_datastore_stats.assert_not_awaited()

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_returns_zero_stats_when_no_datastores_exist(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = []
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertEqual(response_data["datastore_count"], 0)
        self.assertEqual(len(response_data["datastore_ids"]), 0)

        self.cache_mock.set_datastore_stats.assert_awaited_once()
        cached_response = self.cache_mock.set_datastore_stats.call_args[1]["response"]
        self.assertEqual(cached_response.datastore_count, 0)
        self.assertEqual(len(cached_response.datastore_ids), 0)

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_datastore_count_matches_datastore_ids_length(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        datastore_ids = [uuid4() for _ in range(7)]
        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = datastore_ids
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertEqual(response_data["datastore_count"], 7)
        self.assertEqual(len(response_data["datastore_ids"]), 7)
        self.assertEqual(
            response_data["datastore_count"], len(response_data["datastore_ids"])
        )

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_returns_all_datastore_ids_in_response(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        datastore_ids = [uuid4(), uuid4(), uuid4()]
        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = datastore_ids
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        response_data = response.json()
        response_ids = [uuid4_str for uuid4_str in response_data["datastore_ids"]]
        expected_ids = [str(id) for id in datastore_ids]

        self.assertEqual(set(response_ids), set(expected_ids))

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_uses_user_identity_credentials_for_repository_call(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = []
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        repo_instance.get_user_datastore_ids.assert_awaited_once_with(
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id,
        )

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_caches_response_with_correct_user_identity(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = self.datastore_ids
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        self.cache_mock.set_datastore_stats.assert_awaited_once()
        call_kwargs = self.cache_mock.set_datastore_stats.call_args[1]
        self.assertEqual(call_kwargs["user_identity"], user_identity_mock)
        self.assertIsInstance(call_kwargs["response"], DataStoreStatsResponse)

    @patch("integration_service.api.router.datastore_stats_router.DataStoreRepository")
    @patch("integration_service.api.router.datastore_stats_router.get_current_identity")
    def test_handles_single_datastore(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_stats.return_value = None

        single_datastore_id = [uuid4()]
        repo_instance = AsyncMock()
        repo_instance.get_user_datastore_ids.return_value = single_datastore_id
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        response_data = response.json()
        self.assertEqual(response_data["datastore_count"], 1)
        self.assertEqual(len(response_data["datastore_ids"]), 1)
