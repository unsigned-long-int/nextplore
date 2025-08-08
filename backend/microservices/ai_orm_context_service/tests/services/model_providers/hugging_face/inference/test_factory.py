import unittest
from unittest.mock import patch, MagicMock

from services.model_providers.hugging_face.inference.factory import dispatch_inference_provider
from services.exceptions import InferenceProviderMissing


class TestDispatchInferenceProvider(unittest.TestCase):

    @patch('services.model_providers.hugging_face.inference.factory.INFERENCE_REGISTRY', new_callable=dict)
    def test_returns_correct_provider_instance(self, mock_registry):
        mock_provider_class = MagicMock()
        mock_provider_instance = MagicMock()
        mock_provider_class.return_value = mock_provider_instance

        mock_registry['cerebras'] = mock_provider_class

        result = dispatch_inference_provider('cerebras', 'https://fake.url')

        mock_provider_class.assert_called_once_with('cerebras', 'https://fake.url')
        self.assertEqual(result, mock_provider_instance)

    @patch('services.model_providers.hugging_face.inference.factory.INFERENCE_REGISTRY', new_callable=dict)
    def test_raises_exception_when_provider_not_found(self, mock_registry):
        mock_registry.clear()

        with self.assertRaises(InferenceProviderMissing) as context:
            dispatch_inference_provider('unknown', 'https://fake.url')

        self.assertIn('Inference provider not found: unknown', str(context.exception))
