import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from llm_inference_service.api.router.user_llm_test_router import router
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse


MODULE = 'llm_inference_service.api.router.user_llm_test_router'


def make_payload() -> dict:
    return {
        'model_id': 'openai/gpt-4o',
        'api_base': 'https://api.openai.com/v1',
        'connection_params': {'api_key': 'sk-test'},
        'max_tokens': 4096,
        'label': 'Test Model',
    }


class MockUserIdentity:
    def __init__(self, organization_id, user_id):
        self.organization_id = organization_id
        self.user_id = user_id


class TestUserLlmTestRouter(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.user_identity = MockUserIdentity(
            organization_id=self.organization_id,
            user_id=self.user_id,
        )
        self.mock_params = MagicMock()
        self.mock_params.model_id = 'openai/gpt-4o'

    def _url(self, org_id=None, user_id=None) -> str:
        org_id = org_id or self.organization_id
        user_id = user_id or self.user_id
        return f'/v1/llm-inference/organizations/{org_id}/users/{user_id}/llm/test'

    def _mock_provider(self, response: str = 'ok'):
        provider = AsyncMock()
        provider.prompt_model = AsyncMock(return_value=response)
        return provider

    def _mock_factory(self, provider):
        factory = MagicMock()
        factory.create.return_value = provider
        return factory


    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_returns_204_on_success(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        mock_dispatch.return_value = self._mock_factory(self._mock_provider('ok'))

        response = self.client.post(self._url(), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_calls_prompt_model_with_hi_and_max_tokens_1(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        provider = self._mock_provider('ok')
        mock_dispatch.return_value = self._mock_factory(provider)

        self.client.post(self._url(), json=make_payload())

        provider.prompt_model.assert_awaited_once_with('Hi!', max_tokens=1)


    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_converts_payload_to_params(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        mock_dispatch.return_value = self._mock_factory(self._mock_provider('ok'))

        from svc_llm_inference_contracts.models import UserLlmTestRequest
        self.client.post(self._url(), json=make_payload())

        mock_from_dto.assert_called_once_with(UserLlmTestRequest(**make_payload()))

    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_dispatches_with_resolved_params(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        mock_dispatch.return_value = self._mock_factory(self._mock_provider('ok'))

        self.client.post(self._url(), json=make_payload())

        mock_dispatch.assert_called_once_with(self.mock_params)


    @patch(f'{MODULE}.get_current_identity')
    def test_returns_403_when_user_id_mismatch(self, mock_identity):
        mock_identity.return_value = self.user_identity

        response = self.client.post(self._url(user_id=uuid4()), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail']['message'], 'Forbidden')

    @patch(f'{MODULE}.get_current_identity')
    def test_returns_403_when_org_id_mismatch(self, mock_identity):
        mock_identity.return_value = self.user_identity

        response = self.client.post(self._url(org_id=uuid4()), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail']['message'], 'Forbidden')

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.get_current_identity')
    def test_logs_forbidden_request(self, mock_identity, mock_logger):
        mock_identity.return_value = self.user_identity

        self.client.post(self._url(org_id=uuid4()), json=make_payload())

        mock_logger.error.assert_called_once()
        self.assertIn('Forbidden', mock_logger.error.call_args.args[0])


    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_returns_424_when_empty_response(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        mock_dispatch.return_value = self._mock_factory(self._mock_provider(''))

        response = self.client.post(self._url(), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertIn('Llm response error', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_returns_424_when_none_response(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        mock_dispatch.return_value = self._mock_factory(self._mock_provider(None))

        response = self.client.post(self._url(), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_returns_424_when_invalid_model_response_raised(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        provider = AsyncMock()
        provider.prompt_model.side_effect = InvalidModelResponse('bad response')
        mock_dispatch.return_value = self._mock_factory(provider)

        response = self.client.post(self._url(), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)
        self.assertIn('Llm response error', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_returns_500_on_unexpected_error(self, mock_from_dto, mock_dispatch, mock_identity):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        provider = AsyncMock()
        provider.prompt_model.side_effect = RuntimeError('network timeout')
        mock_dispatch.return_value = self._mock_factory(provider)

        response = self.client.post(self._url(), json=make_payload())

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Unexpected error', response.json()['detail']['message'])
        self.assertIn('network timeout', response.json()['detail']['message'])

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_logs_unexpected_error_with_exc_info(self, mock_from_dto, mock_dispatch, mock_identity, mock_logger):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        provider = AsyncMock()
        provider.prompt_model.side_effect = RuntimeError('unexpected')
        mock_dispatch.return_value = self._mock_factory(provider)

        self.client.post(self._url(), json=make_payload())

        mock_logger.error.assert_called_once()
        self.assertTrue(mock_logger.error.call_args.kwargs['exc_info'])

    @patch(f'{MODULE}.logger')
    @patch(f'{MODULE}.get_current_identity')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.user_llm_params_from_dto')
    def test_logs_unexpected_error_context(self, mock_from_dto, mock_dispatch, mock_identity, mock_logger):
        mock_identity.return_value = self.user_identity
        mock_from_dto.return_value = self.mock_params
        provider = AsyncMock()
        provider.prompt_model.side_effect = RuntimeError('unexpected')
        mock_dispatch.return_value = self._mock_factory(provider)

        self.client.post(self._url(), json=make_payload())

        extra = mock_logger.error.call_args.kwargs['extra']
        self.assertEqual(extra['organization_id'], self.organization_id)
        self.assertEqual(extra['user_id'], self.user_id)
        self.assertEqual(extra['error_type'], 'RuntimeError')


    def test_returns_422_for_invalid_payload(self):
        response = self.client.post(self._url(), json={'invalid': 'payload'})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_returns_422_for_invalid_uuid_in_path(self):
        response = self.client.post(
            f'/v1/llm-inference/organizations/not-a-uuid/users/{self.user_id}/llm/test',
            json=make_payload()
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
