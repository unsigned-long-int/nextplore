import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_llm_inference_contracts.models import (
    ORMContextRequest,
    ORMContextResponse,
    LlmOutputSpecs,
    DataStoreEntry,
    SchemaEntry
)

from llm_inference_service.api.router.orm_context_router import router
from llm_inference_service.services.models_gateway.exceptions import InferenceProviderMissing, InvalidModelResponse
from llm_inference_service.services.models_gateway.models_registry import get_models_registry
from llm_inference_service.cache import get_cache_service


ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
ENDPOINT = f'/v1/llm-inference/organizations/{ORGANIZATION_ID}/users/{USER_ID}/context'
MODULE = 'llm_inference_service.api.router.orm_context_router'


class TestOrmContextRouter(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self.cache_mock = AsyncMock()
        self.models_registry_mock = MagicMock()
        self.app.dependency_overrides = {
            get_cache_service: lambda: self.cache_mock,
            get_models_registry: lambda: self.models_registry_mock,
        }

        self.mock_identity = MagicMock()
        self.mock_identity.organization_id = ORGANIZATION_ID
        self.mock_identity.user_id = USER_ID

        self.mock_provider_params = MagicMock()

        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            llm_output_specs=LlmOutputSpecs(
                datastore_registry_repr='general',
                datastores_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=['marvel', 'dc', 'startrek'],
                tables_enum=['characters', 'relatives', 'realms'],
                columns_enum=['power', 'skills', 'age', 'height', 'weight', 'name'],
                filter_op_enum=['=', '>', '<', '!='],
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max'],
                table_columns_registry={
                    str(uuid.uuid4()): DataStoreEntry(schemas={
                        'marvel': SchemaEntry(tables={
                            'characters': ['power', 'skills', 'age', 'height', 'weight', 'name']
                        })
                    })
                }
            )
        )

        self.orm_context = ORMContextResponse(
            datastore=uuid.uuid4(),
            schema_name='marvel',
            class_name='MarvelCharacters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'agg_func': 'count', 'agg_column': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )

        self.mock_provider = AsyncMock()
        self.mock_provider.execute_structured_query.return_value = 'raw-model-response'

        self.mock_factory = MagicMock()
        self.mock_factory.create.return_value = self.mock_provider

        self.cache_mock.get_orm_context = AsyncMock(return_value=None)
        self.cache_mock.set_orm_context = AsyncMock()


    @patch(f'{MODULE}.get_current_identity')
    def test_returns_cached_orm_context(self, mock_identity):
        mock_identity.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = self.orm_context

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.orm_context, ORMContextResponse(**response.json()))

    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_set_cache_on_cache_hit(self, mock_identity):
        mock_identity.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        self.cache_mock.set_orm_context.assert_not_awaited()

    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_resolve_params_on_cache_hit(self, mock_identity, mock_resolve):
        mock_identity.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        mock_resolve.assert_not_called()


    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_200_on_cache_miss(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.return_value = self.orm_context

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.orm_context, ORMContextResponse(**response.json()))

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_resolves_provider_params_with_correct_args(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        mock_resolve.assert_called_once_with(
            payload=self.request,
            models_registry=self.models_registry_mock,
        )

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_dispatches_provider_with_resolved_params(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        mock_dispatch.assert_called_once_with(self.mock_provider_params)

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_executes_structured_query_with_payload(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        self.mock_provider.execute_structured_query.assert_awaited_once_with(self.request)

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_adapts_raw_model_response(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        mock_adapt.assert_called_once_with('raw-model-response')

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_sets_cache_with_correct_args(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.return_value = self.orm_context

        self.client.post(ENDPOINT, json=self.request.model_dump())

        self.cache_mock.set_orm_context.assert_awaited_once_with(
            user_identity=self.mock_identity,
            request=self.request,
            response=self.orm_context,
        )


    @patch(f'{MODULE}.get_current_identity')
    def test_forbidden_when_organization_id_mismatch(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = uuid.uuid4()
        mismatched.user_id = USER_ID
        mock_identity.return_value = mismatched

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_forbidden_when_user_id_mismatch(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = ORGANIZATION_ID
        mismatched.user_id = uuid.uuid4()
        mock_identity.return_value = mismatched

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_call_cache_on_forbidden(self, mock_identity):
        mismatched = MagicMock()
        mismatched.organization_id = uuid.uuid4()
        mismatched.user_id = uuid.uuid4()
        mock_identity.return_value = mismatched

        self.client.post(ENDPOINT, json=self.request.model_dump())

        self.cache_mock.get_orm_context.assert_not_awaited()


    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_424_when_inference_provider_missing(self, mock_identity, mock_resolve, mock_dispatch):
        mock_identity.return_value = self.mock_identity
        mock_resolve.side_effect = InferenceProviderMissing('Provider missing')

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(424, response.status_code)
        self.assertIn('Provider missing', response.json()['detail']['message'])

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_424_when_invalid_model_response(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.side_effect = InvalidModelResponse('Bad response shape')

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(424, response.status_code)
        self.assertIn('Bad response shape', response.json()['detail']['message'])

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_returns_500_on_unexpected_exception(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.side_effect = RuntimeError('Unexpected exception')

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected exception', response.json()['detail']['message'])

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_cache_on_provider_error(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.side_effect = InvalidModelResponse('bad response')

        self.client.post(ENDPOINT, json=self.request.model_dump())

        self.cache_mock.set_orm_context.assert_not_awaited()

    @patch(f'{MODULE}.adapt_llm_response')
    @patch(f'{MODULE}.dispatch_provider_factory')
    @patch(f'{MODULE}.resolve_llm_provider_params')
    @patch(f'{MODULE}.get_current_identity')
    def test_does_not_cache_on_unexpected_error(self, mock_identity, mock_resolve, mock_dispatch, mock_adapt):
        mock_identity.return_value = self.mock_identity
        mock_resolve.return_value = self.mock_provider_params
        mock_dispatch.return_value = self.mock_factory
        mock_adapt.side_effect = RuntimeError('boom')

        self.client.post(ENDPOINT, json=self.request.model_dump())

        self.cache_mock.set_orm_context.assert_not_awaited()
