import unittest
from unittest.mock import patch, MagicMock

from llm_inference_service.services.orm_context.exceptions import InferenceProviderMissing
from llm_inference_service.services.orm_context.model_providers.hugging_face.inference import \
    dispatch_inference_provider


class TestFactory(unittest.TestCase):

    @patch('llm_inference_service.services.orm_context.model_providers.hugging_face.inference.inference_provider_factory.factory.INFERENCE_REGISTRY', new_callable=dict)
    def test_returns_provider_instance(
        self,
        registry_mock
    ):
        provider_class_mock = MagicMock()
        provider_instance_mock = MagicMock()
        provider_class_mock.return_value = provider_instance_mock
        registry_mock['cerebras'] = provider_class_mock

        result = dispatch_inference_provider('cerebras', 'whatever-url')
        provider_class_mock.assert_called_once_with('cerebras', 'whatever-url')
        self.assertEqual(result, provider_instance_mock)

    @patch('llm_inference_service.services.orm_context.model_providers.hugging_face.inference.inference_provider_factory.factory.INFERENCE_REGISTRY', new_callable=dict)
    def test_raises_inference_provider_missing_exception(
        self,
        registry_mock
    ):
        registry_mock.clear()
        self.assertRaises(InferenceProviderMissing, dispatch_inference_provider, 'cerebras', 'whatever-url')
