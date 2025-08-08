import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from services.provider_factory.dispatcher import dispatch_provider_factory
from services.provider_factory.exceptions import MissingModelProviderFactory


class TestDispatchProviderFactory(unittest.TestCase):
    
    def setUp(self):
        self.model_meta: Dict[str, Any] = {
            'model_id': 'mock-model'
        }

    @patch('services.provider_factory.dispatcher.PROVIDER_FACTORY_REGISTRY')
    def test_dispatch_returns_correct_factory(self, mock_registry):
        mock_factory_cls = MagicMock()
        mock_factory_instance = MagicMock()
        mock_factory_cls.return_value = mock_factory_instance

        mock_registry.__contains__.return_value = True
        mock_registry.get.return_value = mock_factory_cls

        provider = 'mock_provider'
        result = dispatch_provider_factory(provider, self.model_meta)

        mock_factory_cls.assert_called_once_with(self.model_meta)
        self.assertEqual(result, mock_factory_instance)

    @patch('services.provider_factory.dispatcher.PROVIDER_FACTORY_REGISTRY', {})
    def test_dispatch_raises_for_missing_provider(self):
        provider = 'unknown_provider'
        with self.assertRaises(MissingModelProviderFactory) as cm:
            dispatch_provider_factory(provider, self.model_meta)
        
        self.assertIn('Model provider factory for provider: unknown_provider not found', str(cm.exception))


if __name__ == '__main__':
    unittest.main()
