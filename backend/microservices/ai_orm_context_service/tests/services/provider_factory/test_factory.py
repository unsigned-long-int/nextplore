import unittest
from unittest.mock import patch, MagicMock

from services.provider_factory.factory import (
    ProviderFactoryBase,
    HFProviderFactory,
    OpenAIProviderFactory
)

HF_META = {
    'model_id': 'hf-test-model',
    'hf_path': 'hf/path/to/model',
    'max_tokens': 1024,
    'inference': 'text-generation',
    'hf_url': 'https://api.fake-hf.com'
}

OPENAI_META = {
    'model_id': 'gpt-4'
}


class TestProviderFactoryBase(unittest.TestCase):

    def test_abstract_base_instantiation_raises(self):
        with self.assertRaises(TypeError):
            ProviderFactoryBase(model_meta={})


class TestHFProviderFactory(unittest.TestCase):

    @patch('services.provider_factory.factory.dispatch_inference_provider')
    @patch('services.provider_factory.factory.HFModel')
    @patch('services.provider_factory.factory.HFProvider')
    def test_create_hf_provider(self, mock_hf_provider, mock_hf_model, mock_dispatch):
        mock_model = MagicMock()
        mock_inference = MagicMock()
        mock_hf_model.return_value = mock_model
        mock_dispatch.return_value = mock_inference
        mock_hf_provider.return_value = 'hf_instance'

        factory = HFProviderFactory(model_meta=HF_META)
        provider = factory.create()

        mock_hf_model.assert_called_once_with(
            model_id='hf-test-model',
            hf_path='hf/path/to/model',
            max_tokens=1024
        )
        mock_dispatch.assert_called_once_with(
            inference='text-generation',
            url='https://api.fake-hf.com'
        )
        mock_hf_provider.assert_called_once_with(
            model=mock_model,
            inference_provider=mock_inference
        )
        self.assertEqual(provider, 'hf_instance')


class TestOpenAIProviderFactory(unittest.TestCase):

    @patch('services.provider_factory.factory.OpenAIProvider')
    def test_create_openai_provider(self, mock_openai_provider):
        mock_openai_provider.return_value = 'openai_instance'

        factory = OpenAIProviderFactory(model_meta=OPENAI_META)
        provider = factory.create()

        mock_openai_provider.assert_called_once_with(model_id='gpt-4')
        self.assertEqual(provider, 'openai_instance')
