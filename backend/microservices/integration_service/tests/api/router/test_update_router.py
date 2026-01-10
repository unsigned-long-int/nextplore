import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import SecretStr

from integration_service.api.router.update_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.integration_update_request import IntegrationUpdateRequest
from integration_service.cache import get_cache_service
from integration_service.database.exceptions import IntegrationUpdateFailed


class TestUpdateIntegrationRouter(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.cache_mock.cache = AsyncMock()
        self.database_backend_connector_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_backend_connector: lambda: self.database_backend_connector_mock,
        }

        self.request = IntegrationUpdateRequest(
            connection_name='updated-connection',
            host='updated-host.com',
            port=5433,
            database_name='updated_db',
            username=SecretStr('updated_user'),
            password=SecretStr('updated_pass'),
            autosync_on=True
        )

    def _url(self, org_id, user_id, integration_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/integrations/{integration_id}'
        )

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_updates_integration_successfully(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        secret_version = 5

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = secret_version
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        integration_update_from_dto_mock.assert_called_once_with(self.request)

        repo_instance.get_latest_version.assert_awaited_once_with(
            integration_id=integration_id,
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id
        )

        secrets_from_dto_mock.assert_called_once_with(
            organization_id=user_identity_mock.organization_id,
            user_id=user_identity_mock.user_id,
            integration_id=integration_id,
            integration_request=self.request,
            version=secret_version + 1
        )

        repo_instance.update_integration.assert_awaited_once_with(
            integration_id=integration_id,
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id,
            integration_update=integration_update_mock,
            secrets=secrets_mock
        )

        self.cache_mock.cache.delete_by_prefix.assert_awaited_once_with(
            user_identity_mock.organization_id,
            user_identity_mock.user_id
        )

    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_user_id = uuid4()
        integration_id = uuid4()

        response = self.client.patch(
            self._url(user_identity_mock.organization_id, different_user_id, integration_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        different_org_id = uuid4()
        integration_id = uuid4()

        response = self.client.patch(
            self._url(different_org_id, user_identity_mock.user_id, integration_id),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_raises_exception_when_get_latest_version_fails(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.side_effect = IntegrationUpdateFailed(
            'Integration not found'
        )
        integration_repo_mock.return_value = repo_instance

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Database error: Integration not found',
            response.json()['detail']['message']
        )

        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_raises_exception_when_update_fails(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        secret_version = 5

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = secret_version
        repo_instance.update_integration.side_effect = IntegrationUpdateFailed('Update failed')
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(424, response.status_code)
        self.assertIn(
            'Database error: Update failed',
            response.json()['detail']['message']
        )

        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_raises_exception_when_generic_error(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()

        integration_update_from_dto_mock.side_effect = RuntimeError('Unexpected error')

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(500, response.status_code)
        self.assertIn(
            'Unexpected error: Unexpected error',
            response.json()['detail']['message']
        )

        self.cache_mock.cache.delete_by_prefix.assert_not_awaited()

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_increments_secret_version_correctly(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        current_version = 10

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = current_version
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        secrets_from_dto_mock.assert_called_once()
        call_kwargs = secrets_from_dto_mock.call_args[1]
        self.assertEqual(call_kwargs['version'], current_version + 1)

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_passes_both_integration_update_and_secrets_to_repository(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        secret_version = 5

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = secret_version
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        repo_instance.update_integration.assert_awaited_once_with(
            integration_id=integration_id,
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id,
            integration_update=integration_update_mock,
            secrets=secrets_mock
        )

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_uses_user_identity_credentials_for_all_operations(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        secret_version = 5

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = secret_version
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        repo_instance.get_latest_version.assert_awaited_once_with(
            integration_id=integration_id,
            user_id=user_identity_mock.user_id,
            organization_id=user_identity_mock.organization_id
        )

        secrets_from_dto_mock.assert_called_once()
        call_kwargs = secrets_from_dto_mock.call_args[1]
        self.assertEqual(call_kwargs['organization_id'], user_identity_mock.organization_id)
        self.assertEqual(call_kwargs['user_id'], user_identity_mock.user_id)

        repo_instance.update_integration.assert_awaited_once()
        update_call_kwargs = repo_instance.update_integration.call_args[1]
        self.assertEqual(update_call_kwargs['user_id'], user_identity_mock.user_id)
        self.assertEqual(update_call_kwargs['organization_id'], user_identity_mock.organization_id)

        self.cache_mock.cache.delete_by_prefix.assert_awaited_once_with(
            user_identity_mock.organization_id,
            user_identity_mock.user_id
        )

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_invalidates_cache_only_after_successful_update(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        secret_version = 5

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = secret_version
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        self.cache_mock.cache.delete_by_prefix.assert_awaited_once()

        repo_instance.update_integration.assert_awaited_once()

    @patch('integration_service.api.router.update_router.secrets_from_dto')
    @patch('integration_service.api.router.update_router.integration_update_from_dto')
    @patch('integration_service.api.router.update_router.IntegrationRepository')
    @patch('integration_service.api.router.update_router.get_current_identity')
    def test_handles_version_zero_correctly(
            self,
            get_current_identity_mock,
            integration_repo_mock,
            integration_update_from_dto_mock,
            secrets_from_dto_mock
    ):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        integration_id = uuid4()
        secret_version = 0

        integration_update_mock = MagicMock()
        integration_update_from_dto_mock.return_value = integration_update_mock

        repo_instance = AsyncMock()
        repo_instance.get_latest_version.return_value = secret_version
        integration_repo_mock.return_value = repo_instance

        secrets_mock = MagicMock()
        secrets_from_dto_mock.return_value = secrets_mock

        response = self.client.patch(
            self._url(
                user_identity_mock.organization_id,
                user_identity_mock.user_id,
                integration_id
            ),
            json=self.request.model_dump(mode='json')
        )

        self.assertEqual(204, response.status_code)

        secrets_from_dto_mock.assert_called_once()
        call_kwargs = secrets_from_dto_mock.call_args[1]
        self.assertEqual(call_kwargs['version'], 1)
