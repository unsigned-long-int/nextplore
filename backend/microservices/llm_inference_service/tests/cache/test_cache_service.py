import unittest
import uuid
from unittest.mock import patch, AsyncMock
from svc_llm_inference_contracts.models import (
    ModelInfo,
    ORMContextResponse,
    ORMContextRequest,
    LlmOutputSpecs,
    IntegrationEntry,
    SchemaEntry
)

from llm_inference_service.cache import CacheService
from llm_inference_service.api.context import UserIdentity


ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


class TestCacheService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.cache = AsyncMock()
        self.cache_service = CacheService(self.cache)
        self.user_identity = UserIdentity(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID
        )
        self.models = [
            ModelInfo(provider='deepseek', model_id='deepseek-12-build', label='DeepSeek', tags=[]),
            ModelInfo(provider='openai', model_id='gpt-4o', label='GPT-4o', tags=['vision']),
        ]
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
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max'],
                table_columns_registry = {
                    str(uuid.uuid4()): IntegrationEntry(schemas={
                        'marvel': SchemaEntry(tables={
                            'characters': ['power', 'skills', 'age', 'height', 'weight', 'name']
                        })
                    })
                }
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

    @patch('llm_inference_service.cache.cache_service.get_string_cache_key', return_value='key123')
    async def test_get_models(self, get_string_cache_key_mock):
        self.cache.get_many.return_value = self.models

        result = await self.cache_service.get_models(user_identity=self.user_identity)

        self.assertEqual(self.models, result)
        get_string_cache_key_mock.assert_called_once_with(value='available-models', prefix='models')
        self.cache.get_many.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, 'key123', model=ModelInfo
        )

    @patch('llm_inference_service.cache.cache_service.get_string_cache_key', return_value='key123')
    async def test_get_models_returns_none_on_cache_miss(self, get_string_cache_key_mock):
        self.cache.get_many.return_value = None

        result = await self.cache_service.get_models(user_identity=self.user_identity)

        self.assertIsNone(result)

    @patch('llm_inference_service.cache.cache_service.get_string_cache_key', return_value='key123')
    async def test_set_models(self, get_string_cache_key_mock):
        await self.cache_service.set_models(
            user_identity=self.user_identity,
            response=self.models
        )

        get_string_cache_key_mock.assert_called_once_with(value='available-models', prefix='models')
        self.cache.set_many.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, 'key123', value=self.models, ttl=600
        )

    @patch('llm_inference_service.cache.cache_service.get_string_cache_key', return_value='key123')
    async def test_set_models_custom_ttl(self, get_string_cache_key_mock):
        await self.cache_service.set_models(
            user_identity=self.user_identity,
            response=self.models,
            ttl=1200
        )

        self.cache.set_many.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, 'key123', value=self.models, ttl=1200
        )

    @patch('llm_inference_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_get_orm_context(self, get_cache_key_mock):
        self.cache.get_one.return_value = self.orm_context

        result = await self.cache_service.get_orm_context(
            user_identity=self.user_identity,
            request=self.request
        )

        self.assertEqual(self.orm_context, result)
        get_cache_key_mock.assert_called_once_with(model=self.request, prefix='orm-context')
        self.cache.get_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, 'key123', model=ORMContextResponse
        )

    @patch('llm_inference_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_get_orm_context_returns_none_on_cache_miss(self, get_cache_key_mock):
        self.cache.get_one.return_value = None

        result = await self.cache_service.get_orm_context(
            user_identity=self.user_identity,
            request=self.request
        )

        self.assertIsNone(result)

    @patch('llm_inference_service.cache.cache_service.get_cache_key', return_value='key123')
    async def test_set_orm_context(self, get_cache_key_mock):
        await self.cache_service.set_orm_context(
            user_identity=self.user_identity,
            request=self.request,
            response=self.orm_context
        )

        get_cache_key_mock.assert_called_once_with(model=self.request, prefix='orm-context')
        self.cache.set_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, 'key123', value=self.orm_context
        )
