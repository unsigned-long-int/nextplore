import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_llm_inference_contracts.models import (
    ORMContextRequest,
    ORMContextResponse,
    LlmOutputSpecs
)

from llm_inference_service.api.router.orm_context_router import router
from llm_inference_service.services.models_gateway.exceptions import InferenceProviderMissing, InvalidModelResponse
from llm_inference_service.services.models_gateway.models_registry import get_models_registry
from llm_inference_service.cache import get_cache_service


ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
ENDPOINT = f'/v1/llm-inference/organizations/{ORGANIZATION_ID}/users/{USER_ID}/context'


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

        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            llm_output_specs=LlmOutputSpecs(
                integration_registry_repr='general',
                integrations_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=['marvel', 'dc', 'startrek'],
                tables_enum=['characters', 'relatives', 'realms'],
                columns_enum=['power', 'skills', 'age', 'height', 'weight', 'name'],
                filter_op_enum=['=', '>', '<', '!='],
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max']
            )
        )

        self.orm_context = ORMContextResponse(
            integration=uuid.uuid4(),
            schema_name='marvel',
            class_name='MarvelCharacters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'agg_func': 'count', 'agg_column': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    def test_returns_cached_orm_context(self, get_current_identity_mock):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = self.orm_context

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.orm_context, ORMContextResponse(**response.json()))
        self.cache_mock.set_orm_context.assert_not_awaited()

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    @patch('llm_inference_service.api.router.orm_context_router.dispatch_provider_factory')
    @patch('llm_inference_service.api.router.orm_context_router.adapt_llm_response')
    def test_builds_orm_context_and_sets_cache(
        self,
        adapt_llm_response_mock,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = None

        mock_provider = AsyncMock()
        mock_factory = MagicMock()
        mock_provider.execute_structured_query.return_value = 'raw-model-response'
        mock_factory.create.return_value = mock_provider
        self.models_registry_mock.get_model.return_value = MagicMock()
        dispatch_provider_factory_mock.return_value = mock_factory
        adapt_llm_response_mock.return_value = self.orm_context

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.orm_context, ORMContextResponse(**response.json()))
        self.models_registry_mock.get_model.assert_called_once_with(
            self.request.provider, self.request.model_id
        )
        dispatch_provider_factory_mock.assert_called_once()
        mock_factory.create.assert_called_once()
        mock_provider.execute_structured_query.assert_awaited_once_with(self.request)
        adapt_llm_response_mock.assert_called_once_with('raw-model-response')
        self.cache_mock.set_orm_context.assert_awaited_once_with(
            user_identity=self.mock_identity,
            request=self.request,
            response=self.orm_context
        )

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    def test_forbidden_when_organization_id_mismatch(self, get_current_identity_mock):
        mismatched_identity = MagicMock()
        mismatched_identity.organization_id = uuid.uuid4()
        mismatched_identity.user_id = USER_ID
        get_current_identity_mock.return_value = mismatched_identity

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(403, response.status_code)
        self.assertIn('Forbidden', response.json()['detail']['message'])

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    def test_forbidden_when_user_id_mismatch(self, get_current_identity_mock):
        mismatched_identity = MagicMock()
        mismatched_identity.organization_id = ORGANIZATION_ID
        mismatched_identity.user_id = uuid.uuid4()
        get_current_identity_mock.return_value = mismatched_identity

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(403, response.status_code)

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    @patch('llm_inference_service.api.router.orm_context_router.dispatch_provider_factory')
    def test_raises_inference_provider_missing(
        self,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = None
        self.models_registry_mock.get_model.side_effect = InferenceProviderMissing('Provider missing')

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(424, response.status_code)
        self.assertIn('Provider missing', response.json()['detail']['message'])

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    @patch('llm_inference_service.api.router.orm_context_router.dispatch_provider_factory')
    @patch('llm_inference_service.api.router.orm_context_router.adapt_llm_response')
    def test_raises_invalid_model_response(
        self,
        adapt_llm_response_mock,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = None

        mock_provider = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_provider
        self.models_registry_mock.get_model.return_value = MagicMock()
        dispatch_provider_factory_mock.return_value = mock_factory
        adapt_llm_response_mock.side_effect = InvalidModelResponse('Bad response shape')

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(424, response.status_code)
        self.assertIn('Bad response shape', response.json()['detail']['message'])

    @patch('llm_inference_service.api.router.orm_context_router.get_current_identity')
    @patch('llm_inference_service.api.router.orm_context_router.dispatch_provider_factory')
    @patch('llm_inference_service.api.router.orm_context_router.adapt_llm_response')
    def test_raises_unexpected_exception(
        self,
        adapt_llm_response_mock,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        get_current_identity_mock.return_value = self.mock_identity
        self.cache_mock.get_orm_context.return_value = None

        mock_provider = AsyncMock()
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_provider
        self.models_registry_mock.get_model.return_value = MagicMock()
        dispatch_provider_factory_mock.return_value = mock_factory
        adapt_llm_response_mock.side_effect = RuntimeError('Unexpected exception')

        response = self.client.post(ENDPOINT, json=self.request.model_dump())

        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected exception', response.json()['detail']['message'])