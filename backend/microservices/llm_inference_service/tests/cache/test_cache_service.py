import unittest
import uuid
from unittest.mock import AsyncMock, patch

from svc_llm_inference_contracts.models import (
    DataStoreEntry,
    LlmOutputSpecs,
    ModelInfo,
    MultiQueryRequest,
    MultiQueryResponse,
    ORMContextRequest,
    ORMContextResponse,
    PromptRequest,
    PromptResponse,
    SchemaEntry,
)

from llm_inference_service.api.context import UserIdentity
from llm_inference_service.cache import CacheService

ORGANIZATION_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


class TestCacheService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.cache = AsyncMock()
        self.cache_service = CacheService(self.cache)
        self.user_identity = UserIdentity(
            organization_id=ORGANIZATION_ID, user_id=USER_ID
        )
        self.models = [
            ModelInfo(
                provider="deepseek",
                model_id="deepseek-12-build",
                label="DeepSeek",
                tags=[],
            ),
            ModelInfo(
                provider="openai", model_id="gpt-4o", label="GPT-4o", tags=["vision"]
            ),
        ]
        self.request = ORMContextRequest(
            provider="Deepseek",
            model_id="Deepseek-14-build",
            query="Count the powers for strong marvel characters",
            llm_output_specs=LlmOutputSpecs(
                datastore_registry_repr="general",
                datastores_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=["marvel", "dc", "startrek"],
                tables_enum=["characters", "relatives", "realms"],
                columns_enum=["power", "skills", "age", "height", "weight", "name"],
                filter_op_enum=["=", ">", "<", "!="],
                agg_funcs_enum=["avg", "sum", "count", "min", "max"],
                table_columns_registry={
                    str(uuid.uuid4()): DataStoreEntry(
                        schemas={
                            "marvel": SchemaEntry(
                                tables={
                                    "characters": [
                                        "power",
                                        "skills",
                                        "age",
                                        "height",
                                        "weight",
                                        "name",
                                    ]
                                }
                            )
                        }
                    )
                },
            ),
        )
        self.orm_context = ORMContextResponse(
            datastore=uuid.uuid4(),
            schema_name="marvel",
            class_name="MarvelCharacters",
            table_name="characters",
            column_names=["name", "power", "skills"],
            column_aggregates=[{"agg_func": "count", "agg_column": "power"}],
            column_filters=[
                {"operator": "=", "value": "strong", "filter_column": "skills"}
            ],
        )
        self.multi_query_request = MultiQueryRequest(
            provider="openai",
            model_id="gpt-4o",
            multiplier=3,
            query="Show me all Klingon characters",
        )

        self.multi_query_response = MultiQueryResponse(
            original_query="Show me all Klingon characters",
            variants=["List Klingon species members"],
        )
        self.prompt_request = PromptRequest(
            prompt="What is the warp speed of the Enterprise?"
        )
        self.prompt_response = PromptResponse(
            response="The Enterprise can reach warp 9.9."
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_string_cache_key",
        return_value="key123",
    )
    async def test_get_models(self, get_string_cache_key_mock):
        self.cache.get_many.return_value = self.models

        result = await self.cache_service.get_models(user_identity=self.user_identity)

        self.assertEqual(self.models, result)
        get_string_cache_key_mock.assert_called_once_with(
            value="available-models", prefix="models"
        )
        self.cache.get_many.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", model=ModelInfo
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_string_cache_key",
        return_value="key123",
    )
    async def test_get_models_returns_none_on_cache_miss(
        self, get_string_cache_key_mock
    ):
        self.cache.get_many.return_value = None

        result = await self.cache_service.get_models(user_identity=self.user_identity)

        self.assertIsNone(result)

    @patch(
        "llm_inference_service.cache.cache_service.get_string_cache_key",
        return_value="key123",
    )
    async def test_set_models(self, get_string_cache_key_mock):
        await self.cache_service.set_models(
            user_identity=self.user_identity, response=self.models
        )

        get_string_cache_key_mock.assert_called_once_with(
            value="available-models", prefix="models"
        )
        self.cache.set_many.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", value=self.models, ttl=600
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_string_cache_key",
        return_value="key123",
    )
    async def test_set_models_custom_ttl(self, get_string_cache_key_mock):
        await self.cache_service.set_models(
            user_identity=self.user_identity, response=self.models, ttl=1200
        )

        self.cache.set_many.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", value=self.models, ttl=1200
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_get_orm_context(self, get_cache_key_mock):
        self.cache.get_one.return_value = self.orm_context

        result = await self.cache_service.get_orm_context(
            user_identity=self.user_identity, request=self.request
        )

        self.assertEqual(self.orm_context, result)
        get_cache_key_mock.assert_called_once_with(
            model=self.request, prefix="orm-context"
        )
        self.cache.get_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", model=ORMContextResponse
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_get_orm_context_returns_none_on_cache_miss(self, get_cache_key_mock):
        self.cache.get_one.return_value = None

        result = await self.cache_service.get_orm_context(
            user_identity=self.user_identity, request=self.request
        )

        self.assertIsNone(result)

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_set_orm_context(self, get_cache_key_mock):
        await self.cache_service.set_orm_context(
            user_identity=self.user_identity,
            request=self.request,
            response=self.orm_context,
        )

        get_cache_key_mock.assert_called_once_with(
            model=self.request, prefix="orm-context"
        )
        self.cache.set_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", value=self.orm_context
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_get_expanded_query(self, get_cache_key_mock):
        self.cache.get_one.return_value = self.multi_query_response

        result = await self.cache_service.get_expanded_query(
            user_identity=self.user_identity, request=self.multi_query_request
        )

        self.assertEqual(self.multi_query_response, result)
        get_cache_key_mock.assert_called_once_with(
            model=self.multi_query_request, prefix="multi-query-response"
        )
        self.cache.get_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", model=MultiQueryResponse
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_get_expanded_query_returns_none_on_cache_miss(
        self, get_cache_key_mock
    ):
        self.cache.get_one.return_value = None

        result = await self.cache_service.get_expanded_query(
            user_identity=self.user_identity, request=self.multi_query_request
        )

        self.assertIsNone(result)

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_set_expanded_query(self, get_cache_key_mock):
        await self.cache_service.set_expanded_query(
            user_identity=self.user_identity,
            request=self.multi_query_request,
            response=self.multi_query_response,
        )

        get_cache_key_mock.assert_called_once_with(
            model=self.multi_query_request, prefix="multi-query-response"
        )
        self.cache.set_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", value=self.multi_query_response
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_get_prompt_response(self, get_cache_key_mock):
        self.cache.get_one.return_value = self.prompt_response

        result = await self.cache_service.get_prompt_response(
            user_identity=self.user_identity, request=self.prompt_request
        )

        self.assertEqual(self.prompt_response, result)
        get_cache_key_mock.assert_called_once_with(
            model=self.prompt_request, prefix="prompt-response"
        )
        self.cache.get_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", model=PromptResponse
        )

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_get_prompt_response_returns_none_on_cache_miss(
        self, get_cache_key_mock
    ):
        self.cache.get_one.return_value = None

        result = await self.cache_service.get_prompt_response(
            user_identity=self.user_identity, request=self.prompt_request
        )

        self.assertIsNone(result)

    @patch(
        "llm_inference_service.cache.cache_service.get_cache_key", return_value="key123"
    )
    async def test_set_prompt_response(self, get_cache_key_mock):
        await self.cache_service.set_prompt_response(
            user_identity=self.user_identity,
            request=self.prompt_request,
            response=self.prompt_response,
        )

        get_cache_key_mock.assert_called_once_with(
            model=self.prompt_request, prefix="prompt-response"
        )
        self.cache.set_one.assert_awaited_once_with(
            ORGANIZATION_ID, USER_ID, "key123", value=self.prompt_response
        )
