import unittest
from unittest.mock import patch, MagicMock

from llm_inference_service.services.models_gateway.model_providers.openai_provider import OpenAiProvider


class TestOpenAiProviderModelPath(unittest.TestCase):

    def test_prefixes_with_openai(self):
        provider = OpenAiProvider('gpt-4o')
        self.assertEqual(provider.model_path(), 'openai/gpt-4o')

    def test_uses_provided_model_id(self):
        provider = OpenAiProvider('gpt-4o-mini')
        self.assertIn('gpt-4o-mini', provider.model_path())


class TestOpenAiProviderBaseKwargs(unittest.TestCase):

    def test_contains_model(self):
        provider = OpenAiProvider('gpt-4o')
        self.assertEqual(provider.base_kwargs()['model'], 'openai/gpt-4o')

    def test_contains_api_key(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test'}):
            provider = OpenAiProvider('gpt-4o')
            self.assertEqual(provider.base_kwargs()['api_key'], 'sk-test')

    def test_empty_string_when_no_env_key(self):
        with patch.dict('os.environ', {}, clear=True):
            provider = OpenAiProvider('gpt-4o')
            self.assertEqual(provider.base_kwargs()['api_key'], '')

    def test_exact_keys(self):
        provider = OpenAiProvider('gpt-4o')
        self.assertSetEqual(
            set(provider.base_kwargs().keys()),
            {'model', 'api_key'}
        )

    def test_does_not_contain_api_base(self):
        provider = OpenAiProvider('gpt-4o')
        self.assertNotIn('api_base', provider.base_kwargs())

    def test_api_key_read_at_construction(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-original'}):
            provider = OpenAiProvider('gpt-4o')
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-changed'}):
            self.assertEqual(provider.base_kwargs()['api_key'], 'sk-original')


class TestOpenAiProviderMaxTokens(unittest.TestCase):

    def _make_model_info(self, max_tokens: int | None) -> MagicMock:
        info = MagicMock()
        info.get.side_effect = lambda key, *args: max_tokens if key == 'max_tokens' else None
        return info

    def test_returns_value_from_litellm(self):
        with patch('llm_inference_service.services.models_gateway.model_providers.openai_provider.litellm') as mock_litellm:
            mock_litellm.get_model_info.return_value = {'max_tokens': 16384}
            provider = OpenAiProvider('gpt-4o')
            self.assertEqual(provider.max_tokens(), 16384)

    def test_falls_back_to_4096_when_litellm_returns_none(self):
        with patch('llm_inference_service.services.models_gateway.model_providers.openai_provider.litellm') as mock_litellm:
            mock_litellm.get_model_info.return_value = {'max_tokens': None}
            provider = OpenAiProvider('gpt-4o')
            self.assertEqual(provider.max_tokens(), 4096)

    def test_falls_back_to_4096_when_key_missing(self):
        with patch('llm_inference_service.services.models_gateway.model_providers.openai_provider.litellm') as mock_litellm:
            mock_litellm.get_model_info.return_value = {}
            provider = OpenAiProvider('gpt-4o')
            self.assertEqual(provider.max_tokens(), 4096)

    def test_calls_get_model_info_with_correct_path(self):
        with patch('llm_inference_service.services.models_gateway.model_providers.openai_provider.litellm') as mock_litellm:
            mock_litellm.get_model_info.return_value = {'max_tokens': 8192}
            provider = OpenAiProvider('gpt-4o-mini')
            provider.max_tokens()
            mock_litellm.get_model_info.assert_called_once_with('openai/gpt-4o-mini')

    def test_zero_max_tokens_falls_back_to_4096(self):
        with patch('llm_inference_service.services.models_gateway.model_providers.openai_provider.litellm') as mock_litellm:
            mock_litellm.get_model_info.return_value = {'max_tokens': 0}
            provider = OpenAiProvider('gpt-4o')
            # 0 is falsy — same as None in current implementation
            self.assertEqual(provider.max_tokens(), 4096)


class TestOpenAiProviderInheritance(unittest.TestCase):

    def test_is_litellm_provider(self):
        from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import LiteLlmProvider
        provider = OpenAiProvider('gpt-4o')
        self.assertIsInstance(provider, LiteLlmProvider)
