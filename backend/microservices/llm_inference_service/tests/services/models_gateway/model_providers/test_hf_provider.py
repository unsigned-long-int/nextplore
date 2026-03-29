import unittest
from unittest.mock import patch

from llm_inference_service.domain.models.model_gateway_params import HFModel
from llm_inference_service.services.models_gateway.model_providers.hf_provider import HFProvider


def make_model(**overrides) -> HFModel:
    defaults = {
        'hf_path': 'meta-llama/Llama-3.1-8B-Instruct',
        'hf_url': 'https://router.huggingface.co/v1',
        'max_tokens': 8192,
        'model_id': 'llama'
    }
    return HFModel(**{**defaults, **overrides})


class TestHFProviderModelPath(unittest.TestCase):

    def test_model_path_prefixes_with_openai(self):
        provider = HFProvider(make_model())
        self.assertEqual(provider.model_path(), 'openai/meta-llama/Llama-3.1-8B-Instruct')

    def test_model_path_uses_hf_path(self):
        provider = HFProvider(make_model(hf_path='deepseek-ai/DeepSeek-V3'))
        self.assertIn('deepseek-ai/DeepSeek-V3', provider.model_path())


class TestHFProviderBaseKwargs(unittest.TestCase):

    def test_base_kwargs_contains_model(self):
        provider = HFProvider(make_model())
        self.assertEqual(
            provider.base_kwargs()['model'],
            'openai/meta-llama/Llama-3.1-8B-Instruct'
        )

    def test_base_kwargs_contains_api_base(self):
        provider = HFProvider(make_model(hf_url='https://router.huggingface.co/v1'))
        self.assertEqual(
            provider.base_kwargs()['api_base'],
            'https://router.huggingface.co/v1'
        )

    def test_base_kwargs_contains_api_key(self):
        with patch.dict('os.environ', {'HUGGINGFACE_API_KEY': 'hf-test-key'}):
            provider = HFProvider(make_model())
            self.assertEqual(provider.base_kwargs()['api_key'], 'hf-test-key')

    def test_base_kwargs_uses_empty_string_when_no_env_key(self):
        with patch.dict('os.environ', {}, clear=True):
            provider = HFProvider(make_model())
            self.assertEqual(provider.base_kwargs()['api_key'], '')

    def test_base_kwargs_does_not_contain_max_tokens(self):
        provider = HFProvider(make_model())
        self.assertNotIn('max_tokens', provider.base_kwargs())

    def test_base_kwargs_keys(self):
        provider = HFProvider(make_model())
        self.assertSetEqual(
            set(provider.base_kwargs().keys()),
            {'model', 'api_key', 'api_base'}
        )


class TestHFProviderMaxTokens(unittest.TestCase):

    def test_max_tokens_returns_model_value(self):
        provider = HFProvider(make_model(max_tokens=8192))
        self.assertEqual(provider.max_tokens(), 8192)

    def test_max_tokens_reflects_model(self):
        provider = HFProvider(make_model(max_tokens=4096))
        self.assertEqual(provider.max_tokens(), 4096)


class TestHFProviderApiKeyIsolation(unittest.TestCase):
    def test_api_key_read_at_construction(self):
        with patch.dict('os.environ', {'HUGGINGFACE_API_KEY': 'hf-original'}):
            provider = HFProvider(make_model())

        with patch.dict('os.environ', {'HUGGINGFACE_API_KEY': 'hf-changed'}):
            self.assertEqual(provider.base_kwargs()['api_key'], 'hf-original')

