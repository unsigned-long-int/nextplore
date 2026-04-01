import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from llm_inference_service.api.router.multi_query_router import router
from llm_inference_service.cache import get_cache_service
from llm_inference_service.services.models_gateway.exceptions import InferenceProviderMissing, InvalidModelResponse
from llm_inference_service.services.models_gateway.models_registry import get_models_registry
from svc_llm_inference_contracts.models import MultiQueryRequest, MultiQueryResponse


ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
ENDPOINT = f'/v1/llm-inference/organizations/{ORGANIZATION_ID}/users/{USER_ID}/query_multiplier'

PAYLOAD = {
    'provider': 'openai',
    'model_id': 'gpt-4o',
    'multiplier': 3,
    'query': 'Show me all Klingon characters',
}

MODULE = 'llm_inference_service.api.router.multi_query_router'


class TestGetExpandedQuery(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        self.cache_mock = AsyncMock()
        self.models_registry_mock = MagicMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_models_registry: lambda: self.models_registry_mock,
        }

        self.mock_identity = MagicMock()
        self.mock_identity.organization_id = ORGANIZATION_ID
        self.mock_identity.user_id = USER_ID

        self.mock_provider = MagicMock()
        self.mock_provider.execute_query = AsyncMock(
            return_value='Klingon warriors list\nKlingon High Council members\nKlingon Empire characters'
        )

        self.mock_provider_factory = MagicMock()
        self.mock_provider_factory.create.return_value = self.mock_provider

        self.mock_provider_params = MagicMock()

        self.cache_mock.get_expanded_query = AsyncMock(return_value=None)
        self.cache_mock.set_expanded_query = AsyncMock()


    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_200_with_multi_query_response(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(200, response.status_code)
        self.assertIn('variants', response.json())

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_original_query_is_first_variant(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(response.json()['variants'][0], PAYLOAD['query'])

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_variants_capped_at_multiplier(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertLessEqual(len(response.json()['variants']), PAYLOAD['multiplier'] + 1)


    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_resolves_provider_params_with_correct_args(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json=PAYLOAD)

        mock_resolve.assert_called_once_with(
            payload=MultiQueryRequest(**PAYLOAD),
            models_registry=self.models_registry_mock,
        )

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_dispatches_provider_with_resolved_params(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json=PAYLOAD)

        mock_dispatch.assert_called_once_with(self.mock_provider_params)

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_expands_query_with_correct_args(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json=PAYLOAD)

        mock_expand.assert_called_once_with(PAYLOAD['query'], PAYLOAD['multiplier'])

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_executes_expanded_query_via_provider(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.mock_provider.execute_query.assert_awaited_once_with('expanded prompt')


    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_cached_response_when_available(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        cached = MultiQueryResponse(variants=['Show me all Klingon characters', 'List Klingons'])
        self.cache_mock.get_expanded_query = AsyncMock(return_value=cached)

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json()['variants'], cached.variants)

    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_call_provider_on_cache_hit(self, mock_identity, mock_resolve, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        self.cache_mock.get_expanded_query = AsyncMock(
            return_value=MultiQueryResponse(variants=['cached query'])
        )

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.mock_provider.execute_query.assert_not_called()

    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_resolve_params_on_cache_hit(self, mock_identity, mock_resolve, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        self.cache_mock.get_expanded_query = AsyncMock(
            return_value=MultiQueryResponse(variants=['cached query'])
        )

        self.client.post(ENDPOINT, json=PAYLOAD)

        mock_resolve.assert_not_called()

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_stores_response_in_cache_on_cache_miss(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.cache_mock.set_expanded_query.assert_awaited_once()

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_cache_lookup_uses_correct_identity_and_payload(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.cache_mock.get_expanded_query.assert_awaited_once_with(
            user_identity=self.mock_identity,
            request=MultiQueryRequest(**PAYLOAD),
        )


    @patch(f'{MODULE}.get_current_identity')
    def test_forbidden_when_organization_id_mismatch(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = uuid.uuid4()
        mismatched.user_id = USER_ID
        mock_identity.return_value = mismatched

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_forbidden_when_user_id_mismatch(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = ORGANIZATION_ID
        mismatched.user_id = uuid.uuid4()
        mock_identity.return_value = mismatched

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_call_cache_on_forbidden(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = uuid.uuid4()
        mismatched.user_id = uuid.uuid4()
        mock_identity.return_value = mismatched

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.cache_mock.get_expanded_query.assert_not_awaited()


    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_424_when_inference_provider_missing(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.execute_query = AsyncMock(
            side_effect=InferenceProviderMissing('openai provider not configured')
        )

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(424, response.status_code)
        self.assertIn('openai provider not configured', response.json()['detail']['message'])

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_424_when_invalid_model_response(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.execute_query = AsyncMock(
            side_effect=InvalidModelResponse('model returned unexpected format')
        )

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(424, response.status_code)
        self.assertIn('model returned unexpected format', response.json()['detail']['message'])

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_500_on_unexpected_exception(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.execute_query = AsyncMock(
            side_effect=RuntimeError('something exploded')
        )

        response = self.client.post(ENDPOINT, json=PAYLOAD)

        self.assertEqual(500, response.status_code)
        self.assertIn('something exploded', response.json()['detail']['message'])

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_cache_on_provider_error(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.execute_query = AsyncMock(
            side_effect=InferenceProviderMissing('missing')
        )

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.cache_mock.set_expanded_query.assert_not_awaited()

    @patch(f'{MODULE}.expand_query', return_value='expanded prompt')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_cache_on_unexpected_error(self, mock_identity, mock_resolve, mock_dispatch, mock_expand):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_provider_factory
        self.mock_provider.execute_query = AsyncMock(
            side_effect=RuntimeError('boom')
        )

        self.client.post(ENDPOINT, json=PAYLOAD)

        self.cache_mock.set_expanded_query.assert_not_awaited()
