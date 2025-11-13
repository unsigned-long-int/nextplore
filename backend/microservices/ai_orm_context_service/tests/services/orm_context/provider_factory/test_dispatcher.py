import unittest
from unittest.mock import MagicMock, patch

from ai_orm_context_service.services.orm_context.exceptions import MissingModelProviderFactory
from ai_orm_context_service.services.orm_context.provider_factory import dispatch_provider_factory


class TestDispatcher(unittest.TestCase):
    @patch('ai_orm_context_service.services.orm_context.provider_factory.dispatcher.PROVIDER_FACTORY_REGISTRY', new_callable=dict)
    def test_successfully_dispatches(
        self,
        provider_registry_mock
    ):
        model_meta_mock = MagicMock()
        provider_cls = MagicMock()
        provider_instance = MagicMock()
        provider_cls.return_value = provider_instance
        provider_registry_mock['huggingface'] = provider_cls
        factory = dispatch_provider_factory('huggingface', model_meta_mock)
        self.assertEqual(factory, provider_instance)
        provider_cls.assert_called_once_with(model_meta_mock)

    @patch('ai_orm_context_service.services.orm_context.provider_factory.dispatcher.PROVIDER_FACTORY_REGISTRY', new_callable=dict)
    def test_raises_if_missing_provider(
        self,
        provider_registry_mock
    ):
        model_meta_mock = MagicMock()
        provider_cls = MagicMock()
        provider_instance = MagicMock()
        provider_cls.return_value = provider_instance
        provider_registry_mock['huggingface'] = provider_cls
        self.assertRaises(MissingModelProviderFactory, dispatch_provider_factory, 'openai', model_meta_mock)
