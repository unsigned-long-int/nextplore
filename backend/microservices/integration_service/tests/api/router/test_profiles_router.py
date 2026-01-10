import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from integration_service.api.router.profiles_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.integration_profile import IntegrationProfile
from integration_service.api.models.auth import Auth
from integration_service.api.models.db import DB
from integration_service.api.models.cloud import Cloud
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import IntegrationGetFailed
from integration_service.domain.exceptions import MissingCloud, MissingDB, MissingAuth


class TestIntegrationProfilesRouter(unittest.TestCase):
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

        self.integration_profile_1 = IntegrationProfile(
            id=uuid4(),
            auth=Auth.PASSWORD_NATIVE,
            cloud=Cloud.AWS,
            db=DB.POSTGRESQL,
            connection_name='test-connection-1',
            database_name='testdb1',
            host='localhost',
            port=5432,
            autosync_on=True
        )

        self.integration_profile_2 = IntegrationProfile(
            id=uuid4(),
            auth=Auth.IAM,
            cloud=Cloud.AZURE,
            db=DB.MYSQL,
            connection_name='test-connection-2',
            database_name='testdb2',
            host='localhost',
            port=3306,
            autosync_on=False
        )

        self.profiles_response = [
            self.integration_profile_1,
            self.integration_profile_2
        ]

    def _url(self, org_id, user_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/integrations/profiles'
        )

    def _create_domain_integration_mock(self, profile: IntegrationProfile):
        integration_mock = MagicMock()
        integration_mock.id = profile.id

        auth_mock = MagicMock()
        auth_mock.value = profile.auth.value if profile.auth.value else 'postgres'
        integration_mock.auth = auth_mock

        cloud_mock = MagicMock()
        cloud_mock.value = profile.cloud if profile.cloud else None
        integration_mock.cloud = cloud_mock

        db_mock = MagicMock()
        db_mock.value = profile.db if profile.db else 'postgres'
        integration_mock.db = db_mock

        integration_mock.connection_name = profile.connection_name
        integration_mock.database_name = profile.database_name
        integration_mock.host = profile.host
        integration_mock.port = profile.port
        integration_mock.autosync_on = profile.autosync_on

        return integration_mock

    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_returns_cached_profiles(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        cached_profiles = self.profiles_response
        self.cache_mock.get_profiles.return_value = cached_profiles

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)
        self.cache_mock.get_profiles.assert_awaited_once_with(
            user_identity=user_identity_mock
        )

        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['connection_name'], 'test-connection-1')
        self.assertEqual(response_data[1]['connection_name'], 'test-connection-2')

        self.cache_mock.set_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.to_dto_db')
    @patch('integration_service.api.router.profiles_router.to_dto_cloud')
    @patch('integration_service.api.router.profiles_router.to_dto_auth')
    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_fetches_and_caches_profiles_when_cache_miss(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        to_dto_auth_mock,
        to_dto_cloud_mock,
        to_dto_db_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        domain_integration_1 = self._create_domain_integration_mock(self.integration_profile_1)
        domain_integration_2 = self._create_domain_integration_mock(self.integration_profile_2)

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.return_value = [
            domain_integration_1,
            domain_integration_2
        ]
        integration_repo_mock.return_value = repo_instance

        to_dto_auth_mock.side_effect = lambda x: x
        to_dto_cloud_mock.side_effect = lambda x: x
        to_dto_db_mock.side_effect = lambda x: x

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        self.cache_mock.get_profiles.assert_awaited_once_with(
            user_identity=user_identity_mock
        )

        repo_instance.get_integration_profiles.assert_awaited_once_with(
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id
        )

        self.assertEqual(to_dto_auth_mock.call_count, 2)
        self.assertEqual(to_dto_cloud_mock.call_count, 2)
        self.assertEqual(to_dto_db_mock.call_count, 2)

        self.cache_mock.set_profiles.assert_awaited_once()
        cached_response = self.cache_mock.set_profiles.call_args[1]['response']
        self.assertEqual(len(cached_response), 2)

        response_data = response.json()
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['connection_name'], 'test-connection-1')
        self.assertEqual(response_data[1]['connection_name'], 'test-connection-2')

    @patch('integration_service.api.router.profiles_router.get_current_identity')
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
        self.assertEqual('Forbidden', response.json()['detail']['message'])

        self.cache_mock.get_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.get_current_identity')
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
        self.assertEqual('Forbidden', response.json()['detail']['message'])

        self.cache_mock.get_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_raises_exception_when_integration_get_failed(
        self,
        get_current_identity_mock,
        integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.side_effect = IntegrationGetFailed(
            'Database connection error'
        )
        integration_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Database error: Database connection error',
            response.json()['detail']['message']
        )

        self.cache_mock.set_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.to_dto_auth')
    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_raises_exception_when_missing_auth(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        to_dto_auth_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        domain_integration = self._create_domain_integration_mock(self.integration_profile_1)

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.return_value = [domain_integration]
        integration_repo_mock.return_value = repo_instance

        to_dto_auth_mock.side_effect = MissingAuth('Auth type not found')

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Mapping error: Auth type not found',
            response.json()['detail']['message']
        )

        self.cache_mock.set_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.to_dto_cloud')
    @patch('integration_service.api.router.profiles_router.to_dto_auth')
    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_raises_exception_when_missing_cloud(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        to_dto_auth_mock,
        to_dto_cloud_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        domain_integration = self._create_domain_integration_mock(self.integration_profile_1)

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.return_value = [domain_integration]
        integration_repo_mock.return_value = repo_instance

        to_dto_auth_mock.side_effect = lambda x: x
        to_dto_cloud_mock.side_effect = MissingCloud('Cloud provider not found')

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Mapping error: Cloud provider not found',
            response.json()['detail']['message']
        )

        self.cache_mock.set_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.to_dto_db')
    @patch('integration_service.api.router.profiles_router.to_dto_cloud')
    @patch('integration_service.api.router.profiles_router.to_dto_auth')
    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_raises_exception_when_missing_db(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        to_dto_auth_mock,
        to_dto_cloud_mock,
        to_dto_db_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        domain_integration = self._create_domain_integration_mock(self.integration_profile_1)

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.return_value = [domain_integration]
        integration_repo_mock.return_value = repo_instance

        to_dto_auth_mock.side_effect = lambda x: x
        to_dto_cloud_mock.side_effect = lambda x: x
        to_dto_db_mock.side_effect = MissingDB('Database type not found')

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Mapping error: Database type not found',
            response.json()['detail']['message']
        )

        self.cache_mock.set_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_raises_exception_when_generic_error(
        self,
        get_current_identity_mock,
        integration_repo_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.side_effect = RuntimeError(
            'Unexpected error occurred'
        )
        integration_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(500, response.status_code)
        self.assertIn(
            'Unexpected error: Unexpected error occurred',
            response.json()['detail']['message']
        )

        self.cache_mock.set_profiles.assert_not_awaited()

    @patch('integration_service.api.router.profiles_router.to_dto_db')
    @patch('integration_service.api.router.profiles_router.to_dto_cloud')
    @patch('integration_service.api.router.profiles_router.to_dto_auth')
    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_returns_empty_list_when_no_profiles_exist(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        to_dto_auth_mock,
        to_dto_cloud_mock,
        to_dto_db_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.return_value = []
        integration_repo_mock.return_value = repo_instance

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [])

        self.cache_mock.set_profiles.assert_awaited_once()
        cached_response = self.cache_mock.set_profiles.call_args[1]['response']
        self.assertEqual(len(cached_response), 0)

        to_dto_auth_mock.assert_not_called()
        to_dto_cloud_mock.assert_not_called()
        to_dto_db_mock.assert_not_called()

    @patch('integration_service.api.router.profiles_router.to_dto_db')
    @patch('integration_service.api.router.profiles_router.to_dto_cloud')
    @patch('integration_service.api.router.profiles_router.to_dto_auth')
    @patch('integration_service.api.router.profiles_router.IntegrationRepository')
    @patch('integration_service.api.router.profiles_router.get_current_identity')
    def test_calls_mappers_with_enum_values(
        self,
        get_current_identity_mock,
        integration_repo_mock,
        to_dto_auth_mock,
        to_dto_cloud_mock,
        to_dto_db_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        self.cache_mock.get_profiles.return_value = None

        domain_integration = self._create_domain_integration_mock(self.integration_profile_1)

        repo_instance = AsyncMock()
        repo_instance.get_integration_profiles.return_value = [domain_integration]
        integration_repo_mock.return_value = repo_instance

        to_dto_auth_mock.return_value = Auth.PASSWORD_NATIVE
        to_dto_cloud_mock.return_value = Cloud.AZURE
        to_dto_db_mock.return_value = DB.POSTGRESQL

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id)
        )

        self.assertEqual(200, response.status_code)

        to_dto_auth_mock.assert_called_once_with(domain_integration.auth.value)
        to_dto_cloud_mock.assert_called_once_with(domain_integration.cloud.value)
        to_dto_db_mock.assert_called_once_with(domain_integration.db.value)
