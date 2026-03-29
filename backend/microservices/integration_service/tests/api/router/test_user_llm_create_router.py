import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from integration_service.api.router.user_llm_create_router import router
from integration_service.api.dependencies import get_llm_service
from integration_service.database.exceptions import UserLlmCreateFailed


MODULE = 'integration_service.api.router.user_llm_create_router'


def make_payload() -> dict:
    return {
        'model_id': 'openai/meta-llama/Llama-3.1-8B-Instruct',
        'label': 'My Llama endpoint',
        'api_base': 'https://router.huggingface.co/v1',
        'connection_params': {'api_key': 'hf-test-key'},
        'max_tokens': 4096,
        'kek_kid': 'https://vault.azure.net/keys/test-key/version',
    }


class TestCreateLlmModelRouter(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.mock_llm_service = AsyncMock()
        self.app.dependency_overrides = {
            get_llm_service: lambda: self.mock_llm_service,
        }

    def _url(self, org_id, user_id) -> str:
        return f'/v1/integration/organizations/{org_id}/users/{user_id}/llm'

    def _make_identity(self):
        identity = MagicMock()
        identity.user_id = uuid4()
        identity.organization_id = uuid4()
        return identity

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_201_on_success(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity

        response = self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=make_payload(),
        )

        self.assertEqual(201, response.status_code)

    @patch(f'{MODULE}.get_current_identity')
    def test_calls_service_with_correct_args(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity

        self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=make_payload(),
        )

        self.mock_llm_service.create_user_llm.assert_awaited_once()
        call_kwargs = self.mock_llm_service.create_user_llm.call_args.kwargs
        self.assertEqual(call_kwargs['user_identity'], identity)

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_403_when_user_id_mismatch(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity
        different_user_id = uuid4()

        response = self.client.post(
            self._url(identity.organization_id, different_user_id),
            json=make_payload(),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_403_when_org_id_mismatch(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity
        different_org_id = uuid4()

        response = self.client.post(
            self._url(different_org_id, identity.user_id),
            json=make_payload(),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual('Forbidden', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_service_not_called_on_forbidden(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity

        self.client.post(
            self._url(uuid4(), identity.user_id),
            json=make_payload(),
        )

        self.mock_llm_service.create_user_llm.assert_not_awaited()

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_424_on_llm_create_failed(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity
        self.mock_llm_service.create_user_llm.side_effect = UserLlmCreateFailed('db error')

        response = self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=make_payload(),
        )

        self.assertEqual(424, response.status_code)
        self.assertIn('Database error: db error', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_500_on_unexpected_error(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity
        self.mock_llm_service.create_user_llm.side_effect = RuntimeError('unexpected')

        response = self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=make_payload(),
        )

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected error', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_422_on_invalid_payload(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity

        response = self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json={'invalid': 'payload'},
        )

        self.assertEqual(422, response.status_code)

    @patch(f'{MODULE}.get_current_identity')
    def test_service_not_called_on_invalid_payload(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity

        self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json={},
        )

        self.mock_llm_service.create_user_llm.assert_not_awaited()

    @patch(f'{MODULE}.get_current_identity')
    def test_response_body_is_empty_on_success(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity

        response = self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=make_payload(),
        )

        self.assertEqual(201, response.status_code)
        self.assertIsNone(response.json())

    @patch(f'{MODULE}.get_current_identity')
    def test_payload_forwarded_to_service(self, mock_identity):
        identity = self._make_identity()
        mock_identity.return_value = identity
        payload = make_payload()

        self.client.post(
            self._url(identity.organization_id, identity.user_id),
            json=payload,
        )

        call_kwargs = self.mock_llm_service.create_user_llm.call_args.kwargs
        forwarded_payload = call_kwargs['payload']
        self.assertEqual(forwarded_payload.model_id, payload['model_id'])
        self.assertEqual(forwarded_payload.label, payload['label'])
        self.assertEqual(forwarded_payload.max_tokens, payload['max_tokens'])

