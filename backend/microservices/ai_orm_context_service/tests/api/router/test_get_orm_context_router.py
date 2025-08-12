import unittest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from api.router.get_orm_context_router import router 
from nextplore_sdk.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest, Context
from nextplore_sdk.contracts.ai_orm_context_service.orm_context_response import ORMContextResponse
from services.exceptions import InferenceProviderMissing, InvalidModelResponse

class TestGetORMContext(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url='https://test'
        )

        self.request = ORMContextRequest(
            provider='test_provider',
            model_id='test_model',
            query='test query',
            context = Context(
                integration_registry_repr='test_repr',
                integrations_enum=['int1', 'int2'],
                schemas_enum=['schem1', 'schem2'],
                tables_enum=['table1', 'table2'],
                columns_enum=['col1', 'col2'],
                filter_op_enum=['=', '>'],
                agg_funcs_enum=['sum', 'avg']
            )
        )

        self.mock_orm_context = ORMContextResponse(
            integration='test_integration',
            schema_name='test_schema',
            class_name='TestClass',
            table_name='test_table',
            column_names=['col1', 'col2'],
            column_aggregates=[{'sum': 'col1'}],
            column_filters=[{'operator': '=', 'value': 25, 'filter_column': 'col2'}]
        )

    @patch('api.router.get_orm_context_router.get_current_identity', return_value='user-123')
    @patch('api.router.get_orm_context_router.ai_orm_context_service_cache')
    @patch('api.router.get_orm_context_router.get_models_registry')
    @patch('api.router.get_orm_context_router.dispatch_provider_factory')
    @patch('api.router.get_orm_context_router.adapt_llm_response')
    async def test_get_context_success(self, mock_adapt, mock_dispatch, mock_get_registry, mock_cache, mock_identity):
        mock_cache.get_orm_context = AsyncMock(return_value=None)
        mock_cache.set_orm_context = AsyncMock()

        mock_model_meta = MagicMock()
        mock_models_registry = MagicMock()
        mock_models_registry.get_model.return_value = mock_model_meta
        mock_get_registry.return_value = mock_models_registry
        self.app.state = mock_models_registry

        mock_provider = AsyncMock()
        mock_provider.retrieve_model_response.return_value = 'raw_model_response'
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_provider
        mock_dispatch.return_value = mock_factory

        mock_adapt.return_value = self.mock_orm_context

        resp = await self.client.post('/v1/ai-orm/get-context', json=self.request.model_dump())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), self.mock_orm_context.model_dump())

        mock_identity.assert_called_once_with()
        mock_cache.get_orm_context.assert_awaited_once()
        mock_provider.retrieve_model_response.assert_awaited_once()
        mock_adapt.assert_called_once_with('raw_model_response')
        mock_cache.set_orm_context.assert_awaited_once()


    @patch('api.router.get_orm_context_router.get_current_identity', return_value='user-123')
    @patch('api.router.get_orm_context_router.ai_orm_context_service_cache')
    @patch('api.router.get_orm_context_router.get_models_registry')
    @patch('api.router.get_orm_context_router.dispatch_provider_factory')
    async def test_inference_provider_missing(self, mock_dispatch, mock_get_registry, mock_cache, mock_identity):
        mock_cache.get_orm_context = AsyncMock(return_value=None)
        mock_cache.set_orm_context = AsyncMock()

        mock_model_meta = MagicMock()
        mock_models_registry = MagicMock()
        mock_models_registry.get_model.return_value = mock_model_meta
        mock_get_registry.return_value = mock_models_registry
        self.app.state = mock_models_registry


        mock_provider = AsyncMock()
        mock_provider.retrieve_model_response.side_effect = InferenceProviderMissing('provider missing')
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_provider
        mock_dispatch.return_value = mock_factory

        resp = await self.client.post('/v1/ai-orm/get-context', json=self.request.model_dump())

        self.assertEqual(resp.status_code, 424)
        self.assertEqual(resp.json()['detail']['message'], 'provider missing')

    @patch('api.router.get_orm_context_router.get_current_identity', return_value='user-123')
    @patch('api.router.get_orm_context_router.ai_orm_context_service_cache')
    @patch('api.router.get_orm_context_router.get_models_registry')
    @patch('api.router.get_orm_context_router.dispatch_provider_factory')
    async def test_invalid_model_response(self, mock_dispatch, mock_get_registry, mock_cache, mock_identity):
        mock_cache.get_orm_context = AsyncMock(return_value=None)
        mock_cache.set_orm_context = AsyncMock()

        mock_model_meta = MagicMock()
        mock_models_registry = MagicMock()
        mock_models_registry.get_model.return_value = mock_model_meta
        mock_get_registry.return_value = mock_models_registry
        self.app.state = mock_models_registry


        mock_provider = AsyncMock()
        mock_provider.retrieve_model_response.side_effect = InvalidModelResponse('invalid response')
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_provider
        mock_dispatch.return_value = mock_factory

        resp = await self.client.post('/v1/ai-orm/get-context', json=self.request.model_dump())

        self.assertEqual(resp.status_code, 424)
        self.assertEqual(resp.json()['detail']['message'], 'invalid response')

    @patch('api.router.get_orm_context_router.get_models_registry')
    @patch('api.router.get_orm_context_router.dispatch_provider_factory')
    async def test_unexpected_exception(self, mock_dispatch_factory, mock_get_registry):
        mock_model_meta = MagicMock()
        mock_models_registry = MagicMock()
        mock_models_registry.get_model.return_value = mock_model_meta
        mock_get_registry.return_value = mock_models_registry
        self.app.state.models_registry = mock_models_registry

        mock_factory = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.retrieve_model_response.side_effect = RuntimeError('something went wrong')
        mock_factory.create.return_value = mock_provider
        mock_dispatch_factory.return_value = mock_factory

        response = await self.client.post('/v1/ai-orm/get-context', json=self.request.model_dump())
        self.assertEqual(response.status_code, 500)
        self.assertIn('Unexpected error', response.json()['detail']['message'])

    @patch('api.router.get_orm_context_router.get_current_identity', return_value='user-123')
    @patch('api.router.get_orm_context_router.dispatch_provider_factory')
    @patch('api.router.get_orm_context_router.get_models_registry')
    @patch('api.router.get_orm_context_router.ai_orm_context_service_cache')
    async def test_returns_cached_orm_response(self, mock_cache, mock_get_registry, mock_dispatch, mock_identity):
        self.app.state = mock_get_registry
        cached = ORMContextResponse(
            integration='test-integration',
            schema_name='test-schema',
            class_name='test-class',
            table_name='test-table',
            column_names=['col1', 'col2'],
            column_aggregates=[{'col1': 'sum'}],
            column_filters=[{'col': 'col1', 'value': 'test', 'operator': '='}],
        )
        mock_cache.get_orm_context = AsyncMock(return_value=cached)
        mock_cache.set_orm_context = AsyncMock()

        resp = await self.client.post('/v1/ai-orm/get-context', json=self.request.model_dump())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), cached.model_dump())

        mock_identity.assert_called_once_with()
        mock_cache.get_orm_context.assert_awaited_once_with(
            user_identity='user-123',
            request=ANY, 
        )
        mock_cache.set_orm_context.assert_not_called()

        mock_get_registry.assert_not_called()
        mock_dispatch.assert_not_called()

    async def asyncTearDown(self):
        await self.client.aclose()

