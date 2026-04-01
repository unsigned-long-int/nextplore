import unittest
from unittest.mock import MagicMock, patch

from llm_inference_service.domain.models.model_gateway_params import (
    PlatformLlmParams,
    UserLlmParams,
)
from llm_inference_service.services.models_gateway.exceptions import MissingModelProviderFactory
from llm_inference_service.services.models_gateway.provider_factory import dispatch_provider_factory


REGISTRY_PATH = 'llm_inference_service.services.models_gateway.provider_factory.dispatcher.PROVIDER_FACTORY_REGISTRY'


def make_platform_params(**overrides) -> PlatformLlmParams:
    defaults = {
        'provider': 'openai',
        'model_id': 'gpt-4o',
        'meta': {'model': 'gpt-4o-config'},
    }
    return PlatformLlmParams(**{**defaults, **overrides})


def make_user_llm_params(**overrides) -> UserLlmParams:
    defaults = {
        'model_id': 'openai/gpt-4o',
        'api_base': 'https://api.openai.com/v1',
        'connection_params': {'api_key': 'sk-test'},
        'max_tokens': 4096,
    }
    return UserLlmParams(**{**defaults, **overrides})



class TestDispatchPlatformParams(unittest.TestCase):

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_returns_factory_instance(self, registry):
        provider_cls = MagicMock()
        registry['openai'] = provider_cls
        params = make_platform_params()

        result = dispatch_provider_factory(params)

        self.assertEqual(result, provider_cls.return_value)

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_calls_factory_with_model_meta(self, registry):
        provider_cls = MagicMock()
        registry['openai'] = provider_cls
        params = make_platform_params(meta={'model': 'gpt-4o-config'})

        dispatch_provider_factory(params)

        provider_cls.assert_called_once_with(model_meta=params.meta)

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_routes_by_provider_name(self, registry):
        openai_cls = MagicMock()
        deepseek_cls = MagicMock()
        registry['openai'] = openai_cls
        registry['deepseek'] = deepseek_cls

        dispatch_provider_factory(make_platform_params(provider='deepseek'))

        deepseek_cls.assert_called_once()
        openai_cls.assert_not_called()

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_raises_missing_factory_when_provider_not_registered(self, registry):
        registry['huggingface'] = MagicMock()

        with self.assertRaises(MissingModelProviderFactory):
            dispatch_provider_factory(make_platform_params(provider='openai'))

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_raises_missing_factory_when_registry_empty(self, registry):
        with self.assertRaises(MissingModelProviderFactory):
            dispatch_provider_factory(make_platform_params())

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_error_message_contains_provider_name(self, registry):
        with self.assertRaises(MissingModelProviderFactory) as ctx:
            dispatch_provider_factory(make_platform_params(provider='openai'))

        self.assertIn('openai', str(ctx.exception))



class TestDispatchUserLlmParams(unittest.TestCase):

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_returns_custom_factory_instance(self, registry):
        custom_cls = MagicMock()
        registry['custom'] = custom_cls
        params = make_user_llm_params()

        result = dispatch_provider_factory(params)

        self.assertEqual(result, custom_cls.return_value)

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_calls_custom_factory_with_params_as_model(self, registry):
        custom_cls = MagicMock()
        registry['custom'] = custom_cls
        params = make_user_llm_params()

        dispatch_provider_factory(params)

        custom_cls.assert_called_once_with(model_meta={'model': params})

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_always_routes_to_custom_key(self, registry):
        custom_cls = MagicMock()
        registry['custom'] = custom_cls

        dispatch_provider_factory(make_user_llm_params(model_id='meta-llama/Llama-3-8b'))

        custom_cls.assert_called_once()

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_raises_missing_factory_when_custom_not_registered(self, registry):
        with self.assertRaises(MissingModelProviderFactory):
            dispatch_provider_factory(make_user_llm_params())

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_error_message_mentions_custom(self, registry):
        with self.assertRaises(MissingModelProviderFactory) as ctx:
            dispatch_provider_factory(make_user_llm_params())

        self.assertIn('custom', str(ctx.exception).lower())

    @patch(REGISTRY_PATH, new_callable=dict)
    def test_does_not_use_platform_registry_key(self, registry):
        registry['openai'] = MagicMock()

        with self.assertRaises(MissingModelProviderFactory):
            dispatch_provider_factory(make_user_llm_params())
