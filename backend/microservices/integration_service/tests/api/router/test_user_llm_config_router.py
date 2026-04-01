import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

import integration_service.api.router.user_llm_config_router
from integration_service.api.router.user_llm_config_router import router
from integration_service.api.dependencies import get_llm_service
from integration_service.database.exceptions import UserLlmGetFailed
from svc_integration_contracts.models import UserLlmConfig


class TestGetUserLlmConfigRouter(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.llm_service_mock = AsyncMock()

        self.app.dependency_overrides = {
            get_llm_service: lambda: self.llm_service_mock,
        }

        self.mock_config = UserLlmConfig(
            api_base='test-api',
            connection_params={'api_key': 'test-api-key'},
            max_tokens=4562,
        )

    def _url(self, org_id, user_id, model_id) -> str:
        return (
            f'/v1/integration/organizations/{org_id}/'
            f'users/{user_id}/llm/{model_id}/config'
        )

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_returns_config_successfully(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()
        self.llm_service_mock.get_user_llm_config.return_value = self.mock_config

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id, model_id)
        )

        self.assertEqual(200, response.status_code)
        self.llm_service_mock.get_user_llm_config.assert_awaited_once_with(
            user_identity=user_identity_mock,
            model_id=model_id,
        )

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_returns_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()
        different_user_id = uuid4()

        response = self.client.get(
            self._url(user_identity_mock.organization_id, different_user_id, model_id)
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])
        self.llm_service_mock.get_user_llm_config.assert_not_awaited()

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_returns_forbidden_when_org_id_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()
        different_org_id = uuid4()

        response = self.client.get(
            self._url(different_org_id, user_identity_mock.user_id, model_id)
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])
        self.llm_service_mock.get_user_llm_config.assert_not_awaited()

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_returns_forbidden_when_both_ids_mismatch(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()

        response = self.client.get(
            self._url(uuid4(), uuid4(), model_id)
        )

        self.assertEqual(403, response.status_code)
        self.llm_service_mock.get_user_llm_config.assert_not_awaited()

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_raises_424_when_user_llm_get_failed(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()
        self.llm_service_mock.get_user_llm_config.side_effect = UserLlmGetFailed(
            'connection timeout'
        )

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id, model_id)
        )

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error: connection timeout', response.json()['detail']['message'])

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_raises_500_on_unexpected_error(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()
        self.llm_service_mock.get_user_llm_config.side_effect = RuntimeError('boom')

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id, model_id)
        )

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error: boom', response.json()['detail']['message'])

    @patch('integration_service.api.router.user_llm_config_router.get_current_identity')
    def test_passes_correct_parameters_to_service(self, get_current_identity_mock):
        user_identity_mock = MagicMock()
        user_identity_mock.user_id = uuid4()
        user_identity_mock.organization_id = uuid4()
        get_current_identity_mock.return_value = user_identity_mock

        model_id = uuid4()
        self.llm_service_mock.get_user_llm_config.return_value = self.mock_config

        response = self.client.get(
            self._url(user_identity_mock.organization_id, user_identity_mock.user_id, model_id)
        )

        self.assertEqual(200, response.status_code)

        self.llm_service_mock.get_user_llm_config.assert_awaited_once()
        call_kwargs = self.llm_service_mock.get_user_llm_config.call_args[1]

        self.assertEqual(call_kwargs['user_identity'], user_identity_mock)
        self.assertEqual(call_kwargs['model_id'], model_id)