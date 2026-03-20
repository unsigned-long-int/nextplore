import unittest
from unittest.mock import patch, MagicMock

from llm_inference_service.services.models_gateway.provider_factory import (
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
    @patch('llm_inference_service.services.orm_context.provider_factory.factory.HFModel')
    @patch('llm_inference_service.services.orm_context.provider_factory.factory.dispatch_inference_provider')
    @patch('llm_inference_service.services.orm_context.provider_factory.factory.HFProvider')
    def test_creates_hf_provider(
        self,
        hf_provider_mock,
        dispatch_inference_provider_mock,
        hf_model_mock
    ):
        model_meta = MagicMock()
        hf_provider_instance = MagicMock()
        hf_provider_mock.return_value = hf_provider_instance
        inference_instance = MagicMock()
        dispatch_inference_provider_mock.return_value = inference_instance
        hf_model_instance = MagicMock()
        hf_model_mock.return_value = hf_model_instance
        hf_provider = HFProviderFactory(model_meta)
        provider = hf_provider.create()
        self.assertEqual(hf_provider_instance, provider)
        hf_provider_mock.assert_called_once_with(
            model=hf_model_instance,
            inference_provider=inference_instance
        )


class TestOpenAIProviderFactory(unittest.TestCase):
    @patch('llm_inference_service.services.orm_context.provider_factory.factory.OpenAIProvider')
    def test_create_openai_provider(
        self,
        open_ai_provider_mock
    ):
        model_meta = {'model_id': 'openai-test-model'}
        openai_provider = OpenAIProviderFactory(model_meta)
        openai_instance = MagicMock
        open_ai_provider_mock.return_value = openai_instance
        provider = openai_provider.create()
        open_ai_provider_mock.assert_called_once_with(
            model_id = 'openai-test-model'
        )
        self.assertEqual(openai_instance, provider)
