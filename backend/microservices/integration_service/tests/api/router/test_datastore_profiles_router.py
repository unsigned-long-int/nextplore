import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_integration_contracts.models import DB, Auth, Cloud, DataStoreProfile

from integration_service.api.dependencies import get_backend_connector
from integration_service.api.router.datastore_profiles_router import router
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import DataStoreGetFailed


class TestDataStoreProfilesRouter(unittest.TestCase):
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

        self.datastore_profile_1 = DataStoreProfile(
            id=uuid4(),
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name="test-connection-1",
            database_name="testdb1",
            host="localhost",
            port=5432,
            autosync_on=True,
        )

        self.datastore_profile_2 = DataStoreProfile(
            id=uuid4(),
            auth=Auth.iam,
            cloud=Cloud.azure,
            db=DB.mysql,
            connection_name="test-connection-2",
            database_name="testdb2",
            host="localhost",
            port=3306,
            autosync_on=False,
        )

        self.profiles_response = [self.datastore_profile_1, self.datastore_profile_2]

    def _url(self, org_id, user_id) -> str:
        return (
            f"/v1/integration/organizations/{org_id}/"
            f"users/{user_id}/datastores/profiles"
        )

    def _create_domain_datastore_mock(self, profile: DataStoreProfile):
        datastore_mock = MagicMock()
        datastore_mock.id = profile.id
        datastore_mock.auth = profile.auth
        datastore_mock.cloud = profile.cloud
        datastore_mock.db = profile.db
        datastore_mock.connection_name = profile.connection_name
        datastore_mock.database_name = profile.database_name
        datastore_mock.host = profile.host
        datastore_mock.port = profile.port
        datastore_mock.autosync_on = profile.autosync_on

        return datastore_mock

    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
    def test_returns_cached_profiles(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cached_profiles = self.profiles_response
        self.cache_mock.get_datastore_profiles.return_value = cached_profiles

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)
        self.cache_mock.get_datastore_profiles.assert_awaited_once_with(
            user_identity=user_identity_mock
        )

        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]["connection_name"], "test-connection-1")
        self.assertEqual(response_data[1]["connection_name"], "test-connection-2")

        self.cache_mock.set_datastore_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_profiles_router.DataStoreRepository"
    )
    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
    def test_fetches_and_caches_profiles_when_cache_miss(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_profiles.return_value = None

        domain_datastore_1 = self._create_domain_datastore_mock(
            self.datastore_profile_1
        )
        domain_datastore_2 = self._create_domain_datastore_mock(
            self.datastore_profile_2
        )

        repo_instance = AsyncMock()
        repo_instance.get_datastore_profiles.return_value = [
            domain_datastore_1,
            domain_datastore_2,
        ]
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )
        print(response.json())
        self.assertEqual(200, response.status_code)

        self.cache_mock.get_datastore_profiles.assert_awaited_once_with(
            user_identity=user_identity_mock
        )

        repo_instance.get_datastore_profiles.assert_awaited_once_with(
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id,
        )

        self.cache_mock.set_datastore_profiles.assert_awaited_once()
        cached_response = self.cache_mock.set_datastore_profiles.call_args[1][
            "response"
        ]
        self.assertEqual(len(cached_response), 2)

        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]["connection_name"], "test-connection-1")
        self.assertEqual(response_data[1]["connection_name"], "test-connection-2")

    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
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

        self.cache_mock.get_datastore_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
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

        self.cache_mock.get_datastore_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_profiles_router.DataStoreRepository"
    )
    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
    def test_raises_exception_when_datastore_get_failed(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_profiles.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_datastore_profiles.side_effect = DataStoreGetFailed(
            "Database connection error"
        )
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            "Database error: Database connection error",
            response.json()["detail"]["message"],
        )

        self.cache_mock.set_datastore_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_profiles_router.DataStoreRepository"
    )
    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
    def test_raises_exception_when_generic_error(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_profiles.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_datastore_profiles.side_effect = RuntimeError(
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

        self.cache_mock.set_datastore_profiles.assert_not_awaited()

    @patch(
        "integration_service.api.router.datastore_profiles_router.DataStoreRepository"
    )
    @patch(
        "integration_service.api.router.datastore_profiles_router.get_current_identity"
    )
    def test_returns_empty_list_when_no_profiles_exist(
        self, get_current_identity_mock, datastore_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_datastore_profiles.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_datastore_profiles.return_value = []
        datastore_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [])

        self.cache_mock.set_datastore_profiles.assert_awaited_once()
        cached_response = self.cache_mock.set_datastore_profiles.call_args[1][
            "response"
        ]
        self.assertEqual(len(cached_response), 0)
