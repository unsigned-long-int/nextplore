import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from svc_ai_orm_context_contracts.models import (
    ORMContextRequest,
    ORMContextResponse,
    Context
)

from ai_orm_context_service.api.router.orm_context_router import router
from ai_orm_context_service.services.orm_context.exceptions import InferenceProviderMissing
from ai_orm_context_service.services.orm_context.models_registry import get_models_registry
from ai_orm_context_service.cache import get_cache_service


class TestGetModels(unittest.TestCase):
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
        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            context=Context(
                integration_registry_repr='general',
                integrations_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=['marvel', 'dc', 'startrek'],
                tables_enum=['characters', 'relatives', 'realms'],
                columns_enum=['power', 'skills', 'age', 'height', 'weight', 'skills', 'name'],
                filter_op_enum=['=', '>', '<', '!='],
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max']
            )
        )


    @patch('ai_orm_context_service.api.router.orm_context_router.get_current_identity', return_value='no-matter')
    def test_returns_cached_orm_context(self, get_current_identity_mock):
        cached = ORMContextResponse(
            integration=uuid.uuid4(),
            schema_name='marvel',
            class_name='marvel_characters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'count': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )
        self.cache_mock.get_orm_context.return_value = cached
        response = self.client.post('/v1/ai-orm/context', json=self.request.model_dump())
        self.assertEqual(200, response.status_code)
        self.assertEqual(cached, ORMContextResponse(**response.json()))

    @patch('ai_orm_context_service.api.router.orm_context_router.get_current_identity')
    @patch('ai_orm_context_service.api.router.orm_context_router.dispatch_provider_factory')
    @patch('ai_orm_context_service.api.router.orm_context_router.adapt_llm_response')
    def test_builds_orm_context_and_sets_cache(
        self,
        adapt_llm_response_mock,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        orm_context = ORMContextResponse(
            integration=uuid.uuid4(),
            schema_name='marvel',
            class_name='marvel_characters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'count': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )
        self.cache_mock.get_orm_context.return_value = None
        mock_meta = MagicMock()
        mock_provider = AsyncMock()
        mock_factory = MagicMock()
        mock_provider.retrieve_model_response.return_value = 'no-matter'
        mock_factory.create.return_value = mock_provider
        self.models_registry_mock.get_model.return_value = mock_meta
        dispatch_provider_factory_mock.return_value = mock_factory
        get_current_identity_mock.return_value = 'no-matter'
        adapt_llm_response_mock.return_value = orm_context
        response = self.client.post('/v1/ai-orm/context', json=self.request.model_dump())

        self.assertEqual(200, response.status_code)
        self.assertEqual(orm_context, ORMContextResponse(**response.json()))
        get_current_identity_mock.assert_called_once()
        self.models_registry_mock.get_model.assert_called_once()
        dispatch_provider_factory_mock.assert_called_once()
        mock_factory.create.assert_called_once()
        mock_provider.retrieve_model_response.assert_awaited_once_with(self.request)
        adapt_llm_response_mock.assert_called_once_with('no-matter')
        self.cache_mock.set_orm_context.assert_awaited_once_with(
            user_identity='no-matter',
            request=self.request,
            response=orm_context
        )

    @patch('ai_orm_context_service.api.router.orm_context_router.get_current_identity')
    @patch('ai_orm_context_service.api.router.orm_context_router.dispatch_provider_factory')
    @patch('ai_orm_context_service.api.router.orm_context_router.adapt_llm_response')
    def test_raises_inference_provider_missing(
        self,
        adapt_llm_response_mock,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        orm_context = ORMContextResponse(
            integration=uuid.uuid4(),
            schema_name='marvel',
            class_name='marvel_characters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'count': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )
        self.cache_mock.get_orm_context.return_value = None
        mock_provider = AsyncMock()
        mock_factory = MagicMock()
        mock_provider.retrieve_model_response.return_value = 'no-matter'
        mock_factory.create.return_value = mock_provider
        self.models_registry_mock.get_model.side_effect = InferenceProviderMissing('Provider missing')
        dispatch_provider_factory_mock.return_value = mock_factory
        get_current_identity_mock.return_value = 'no-matter'
        adapt_llm_response_mock.return_value = orm_context
        response = self.client.post('/v1/ai-orm/context', json=self.request.model_dump())

        self.assertEqual(424, response.status_code)
        self.assertIn('Provider missing', response.json()['detail']['message'])

    @patch('ai_orm_context_service.api.router.orm_context_router.get_current_identity')
    @patch('ai_orm_context_service.api.router.orm_context_router.dispatch_provider_factory')
    @patch('ai_orm_context_service.api.router.orm_context_router.adapt_llm_response')
    def test_raises_unexpected_exception(
        self,
        adapt_llm_response_mock,
        dispatch_provider_factory_mock,
        get_current_identity_mock
    ):
        self.cache_mock.get_orm_context.return_value = None
        mock_provider = AsyncMock()
        mock_factory = MagicMock()
        mock_meta = MagicMock()
        mock_provider.retrieve_model_response.return_value = 'no-matter'
        mock_factory.create.return_value = mock_provider
        self.models_registry_mock.get_model.return_value = mock_meta
        dispatch_provider_factory_mock.return_value = mock_factory
        get_current_identity_mock.return_value = 'no-matter'
        adapt_llm_response_mock.side_effect = RuntimeError('Unexpected exception')
        response = self.client.post('/v1/ai-orm/context', json=self.request.model_dump())
        self.assertEqual(500, response.status_code)
        self.assertIn('Unexpected exception', response.json()['detail']['message'])
