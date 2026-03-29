import unittest

from llm_inference_service.domain.models.model_gateway_params import UserLlm
from llm_inference_service.services.models_gateway.model_providers.user_llm_provider import UserLlmProvider
from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import LiteLlmProvider


def make_model(**overrides) -> UserLlm:
    defaults = {
        'model_id': 'meta-llama/Llama-3.1-8B-Instruct',
        'max_tokens': 4096,
        'api_base': 'https://my-endpoint.com/v1',
        'connection_params': {
            'api_key': 'test-key',
        },
    }
    return UserLlm(**{**defaults, **overrides})


class TestUserProviderModelPath(unittest.TestCase):

    def test_prefixes_with_openai(self):
        provider = UserLlmProvider(make_model())
        self.assertEqual(provider.model_path(), 'openai/meta-llama/Llama-3.1-8B-Instruct')

    def test_uses_model_id(self):
        provider = UserLlmProvider(make_model(model_id='deepseek-ai/DeepSeek-V3'))
        self.assertEqual(provider.model_path(), 'openai/deepseek-ai/DeepSeek-V3')

    def test_model_path_changes_with_model_id(self):
        provider_a = UserLlmProvider(make_model(model_id='model-a'))
        provider_b = UserLlmProvider(make_model(model_id='model-b'))
        self.assertNotEqual(provider_a.model_path(), provider_b.model_path())


class TestUserLlmProviderBaseKwargs(unittest.TestCase):

    def test_contains_model(self):
        provider = UserLlmProvider(make_model())
        self.assertEqual(
            provider.base_kwargs()['model'],
            'openai/meta-llama/Llama-3.1-8B-Instruct'
        )

    def test_spreads_connection_params(self):
        provider = UserLlmProvider(make_model(connection_params={
            'api_key': 'sk-secret',
        }))
        kwargs = provider.base_kwargs()
        self.assertEqual(kwargs['api_key'], 'sk-secret')

    def test_connection_params_override_nothing_critical(self):
        provider = UserLlmProvider(make_model(connection_params={
            'api_key': 'sk-secret',
        }))
        self.assertEqual(provider.base_kwargs()['model'], 'openai/meta-llama/Llama-3.1-8B-Instruct')

    def test_empty_connection_params(self):
        provider = UserLlmProvider(make_model(connection_params={}))
        kwargs = provider.base_kwargs()
        self.assertSetEqual(set(kwargs.keys()), {'model', 'api_base'})

    def test_arbitrary_connection_params_passed_through(self):
        provider = UserLlmProvider(make_model(connection_params={
            'aws_access_key_id': 'AKIA...',
            'aws_secret_access_key': 'secret',
            'aws_region_name': 'eu-central-1',
        }))
        kwargs = provider.base_kwargs()
        self.assertEqual(kwargs['aws_access_key_id'], 'AKIA...')
        self.assertEqual(kwargs['aws_secret_access_key'], 'secret')
        self.assertEqual(kwargs['aws_region_name'], 'eu-central-1')

    def test_does_not_contain_max_tokens(self):
        provider = UserLlmProvider(make_model(connection_params={}))
        self.assertNotIn('max_tokens', provider.base_kwargs())


class TestUserLlmProviderMaxTokens(unittest.TestCase):

    def test_returns_model_max_tokens(self):
        provider = UserLlmProvider(make_model(max_tokens=8192))
        self.assertEqual(provider.max_tokens(), 8192)

    def test_reflects_model_value(self):
        provider = UserLlmProvider(make_model(max_tokens=2048))
        self.assertEqual(provider.max_tokens(), 2048)


class TestUserLlmProviderInheritance(unittest.TestCase):

    def test_is_litellm_provider(self):
        provider = UserLlmProvider(make_model())
        self.assertIsInstance(provider, LiteLlmProvider)


class TestUserLlmProviderConnectionParamsPrecedence(unittest.TestCase):
    def test_connection_params_model_key_overrides_model_path(self):
        provider = UserLlmProvider(make_model(connection_params={
            'model': 'rogue-model',
            'api_key': 'key',
        }))
        self.assertEqual(provider.base_kwargs()['model'], 'rogue-model')

