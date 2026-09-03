import unittest
from unittest.mock import MagicMock

from svc_llm_inference_contracts.models import (
    MultiQueryRequest,
    ORMContextRequest,
    UserLlmConfig,
    UserLlmTestRequest,
)

from llm_inference_service.domain.mappers.model_gateway_params import (
    resolve_llm_provider_params,
    user_llm_params_from_dto,
)
from llm_inference_service.domain.models.model_gateway_params import (
    PlatformLlmParams,
    UserLlmParams,
)


def make_user_llm_test_request(**overrides) -> UserLlmTestRequest:
    defaults = {
        "model_id": "openai/gpt-4o",
        "api_base": "https://api.openai.com/v1",
        "connection_params": {"api_key": "sk-test"},
        "max_tokens": 4096,
        "label": "Test Model",
    }
    return UserLlmTestRequest(**{**defaults, **overrides})


def make_multi_query_request(**overrides) -> MultiQueryRequest:
    defaults = {
        "provider": "openai",
        "model_id": "gpt-4o",
        "multiplier": 3,
        "query": "Show me all Klingon characters",
        "user_llm_config": None,
    }
    return MultiQueryRequest(**{**defaults, **overrides})


def make_user_llm_config(**overrides) -> UserLlmConfig:
    defaults = {
        "api_base": "https://custom.endpoint.com/v1",
        "connection_params": {"api_key": "custom-key"},
        "max_tokens": 8192,
    }
    return UserLlmConfig(**{**defaults, **overrides})


def make_models_registry(meta=None) -> MagicMock:
    registry = MagicMock()
    registry.get_model.return_value = meta or {"model": "gpt-4o-config"}
    return registry


class TestUserLlmParamsFromDto(unittest.TestCase):
    def setUp(self):
        self.request = make_user_llm_test_request()

    def test_returns_user_llm_params(self):
        result = user_llm_params_from_dto(self.request)
        self.assertIsInstance(result, UserLlmParams)

    def test_maps_model_id(self):
        result = user_llm_params_from_dto(self.request)
        self.assertEqual(result.model_id, self.request.model_id)

    def test_maps_api_base(self):
        result = user_llm_params_from_dto(self.request)
        self.assertEqual(result.api_base, self.request.api_base)

    def test_maps_connection_params(self):
        result = user_llm_params_from_dto(self.request)
        self.assertEqual(result.connection_params, self.request.connection_params)

    def test_maps_max_tokens(self):
        result = user_llm_params_from_dto(self.request)
        self.assertEqual(result.max_tokens, self.request.max_tokens)

    def test_maps_custom_model_id(self):
        request = make_user_llm_test_request(model_id="meta-llama/Llama-3-8b")
        result = user_llm_params_from_dto(request)
        self.assertEqual(result.model_id, "meta-llama/Llama-3-8b")

    def test_maps_custom_api_base(self):
        request = make_user_llm_test_request(
            api_base="https://router.huggingface.co/v1"
        )
        result = user_llm_params_from_dto(request)
        self.assertEqual(result.api_base, "https://router.huggingface.co/v1")

    def test_maps_custom_connection_params(self):
        params = {"api_key": "hf-abc123", "timeout": 30}
        request = make_user_llm_test_request(connection_params=params)
        result = user_llm_params_from_dto(request)
        self.assertEqual(result.connection_params, params)

    def test_maps_custom_max_tokens(self):
        request = make_user_llm_test_request(max_tokens=2048)
        result = user_llm_params_from_dto(request)
        self.assertEqual(result.max_tokens, 2048)


class TestResolveLlmProviderParamsPlatform(unittest.TestCase):
    def setUp(self):
        self.mock_meta = {"model": "gpt-4o-config"}
        self.registry = make_models_registry(meta=self.mock_meta)
        self.request = make_multi_query_request()

    def test_returns_platform_llm_params(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertIsInstance(result, PlatformLlmParams)

    def test_maps_model_id(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(result.model_id, self.request.model_id)

    def test_maps_provider(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(result.provider, self.request.provider)

    def test_maps_meta_from_registry(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(result.meta, self.mock_meta)

    def test_calls_registry_with_correct_provider_and_model_id(self):
        resolve_llm_provider_params(self.request, self.registry)
        self.registry.get_model.assert_called_once_with(
            self.request.provider,
            self.request.model_id,
        )

    def test_does_not_return_user_llm_params_for_platform(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertNotIsInstance(result, UserLlmParams)

    def test_works_with_orm_context_request(self):
        from svc_llm_inference_contracts.models import LlmOutputSpecs

        orm_request = ORMContextRequest(
            provider="deepseek",
            model_id="deepseek-14b",
            query="Count marvel characters",
            llm_output_specs=LlmOutputSpecs(
                datastore_registry_repr="general",
                datastores_enum=[],
                schemas_enum=[],
                tables_enum=[],
                columns_enum=[],
                filter_op_enum=[],
                agg_funcs_enum=[],
                table_columns_registry={},
            ),
        )
        result = resolve_llm_provider_params(orm_request, self.registry)
        self.assertIsInstance(result, PlatformLlmParams)
        self.assertEqual(result.provider, "deepseek")


class TestResolveLlmProviderParamsCustom(unittest.TestCase):
    def setUp(self):
        self.registry = make_models_registry()
        self.user_llm_config = make_user_llm_config()
        self.request = make_multi_query_request(user_llm_config=self.user_llm_config)

    def test_returns_user_llm_params(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertIsInstance(result, UserLlmParams)

    def test_maps_model_id_from_payload(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(result.model_id, self.request.model_id)

    def test_maps_api_base_from_config(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(result.api_base, self.user_llm_config.api_base)

    def test_maps_connection_params_from_config(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(
            result.connection_params, self.user_llm_config.connection_params
        )

    def test_maps_max_tokens_from_config(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertEqual(result.max_tokens, self.user_llm_config.max_tokens)

    def test_does_not_call_registry_for_custom_model(self):
        resolve_llm_provider_params(self.request, self.registry)
        self.registry.get_model.assert_not_called()

    def test_does_not_return_platform_params_for_custom(self):
        result = resolve_llm_provider_params(self.request, self.registry)
        self.assertNotIsInstance(result, PlatformLlmParams)
