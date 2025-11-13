import unittest
import uuid
from unittest.mock import patch, AsyncMock

from ai_orm_context_service.cache import CacheService
from ai_orm_context_service.api.context import UserIdentity
from ai_orm_context_service.api.models.model_info import ModelInfo
from ai_orm_context_service.api.models.orm_context_response import ORMContextResponse
from ai_orm_context_service.api.models.orm_context_request import ORMContextRequest, Context


class TestCacheService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.cache = AsyncMock()
        self.cache_service = CacheService(self.cache)

    @patch('ai_orm_context_service.cache.cache_service.get_string_cache_key', return_value='key123')
    async def test_get_models(
        self,
        get_string_cache_key_mock
    ):
        cached = [
            ModelInfo(
                provider='deepseek',
                model_id='deepseek-12-build',
                label='DeepSeek',
                tags=[]
            )
        ]
        self.cache.get_many.return_value = cached
        result = await self.cache_service.get_models()
        self.assertEqual(cached, result)
        get_string_cache_key_mock.assert_called_once_with(value='available-models', prefix='models')
        self.cache.get_many.assert_awaited_once_with('key123', model=ModelInfo)

    @patch('ai_orm_context_service.cache.cache_service.get_string_cache_key', return_value='key123')
    async def test_set_models(
        self,
        get_string_cache_key_mock
    ):
        response = [
            ModelInfo(
                provider='deepseek',
                model_id='deepseek-12-build',
                label='DeepSeek',
                tags=[]
            )
        ]
        get_string_cache_key_mock.return_value = 'key123'
        await self.cache_service.set_models(response)
        get_string_cache_key_mock.assert_called_once_with(value='available-models', prefix='models')
        self.cache.set_many.assert_awaited_once_with('key123', value=response, ttl=600)

    @patch('ai_orm_context_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_get_orm_context(
        self,
        get_cache_key_mock
    ):
        cached = ORMContextResponse(
            integration=uuid.uuid4(),
            schema_name='marvel',
            class_name='marvel_characters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'count': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )
        request = ORMContextRequest(
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
        self.cache.get_one.return_value = cached

        organization_id = uuid.uuid4()
        user_id = uuid.uuid4()
        result = await self.cache_service.get_orm_context(
            user_identity=UserIdentity(organization_id=organization_id, user_id=user_id),
            request=request
        )
        self.assertEqual(cached, result)
        get_cache_key_mock.assert_called_once_with(model=request, prefix='orm-context')
        self.cache.get_one.assert_awaited_once_with(organization_id, user_id, 'key123', model=ORMContextResponse)

    @patch('ai_orm_context_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_set_orm_context(
        self,
        get_cache_key_mock
    ):
        response = ORMContextResponse(
            integration=uuid.uuid4(),
            schema_name='marvel',
            class_name='marvel_characters',
            table_name='characters',
            column_names=['name', 'power', 'skills'],
            column_aggregates=[{'count': 'power'}],
            column_filters=[{'operator': '=', 'value': 'strong', 'filter_column': 'skills'}]
        )
        request = ORMContextRequest(
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
        organization_id = uuid.uuid4()
        user_id = uuid.uuid4()
        await self.cache_service.set_orm_context(
            user_identity=UserIdentity(organization_id=organization_id, user_id=user_id),
            request=request,
            response=response
        )
        get_cache_key_mock.assert_called_once_with(model=request, prefix='orm-context')
        self.cache.set_one.assert_awaited_once_with(
            organization_id, user_id, 'key123', value=response
        )

