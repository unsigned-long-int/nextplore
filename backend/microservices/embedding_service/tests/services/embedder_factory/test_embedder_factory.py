import unittest
from unittest.mock import patch

from services.embedder_factory.embedder_factory import dispatch_embedder
from services.exceptions import MissingEmbedderEngine
from services.embedders.embedder_base import EmbedderBase


class TestDispatchEmbedder(unittest.TestCase):

    @patch('services.embedder_factory.embedder_factory.EMBEDDERS_REGISTRY', new_callable=dict)
    def test_returns_embedder_for_known_engine(self, mock_registry):
        class FakeEmbedder(EmbedderBase):
            pass

        mock_registry['open_ai'] = FakeEmbedder

        embedder_cls = dispatch_embedder('open_ai')

        self.assertIs(embedder_cls, FakeEmbedder)
        self.assertTrue(issubclass(embedder_cls, EmbedderBase))

    @patch('services.embedder_factory.embedder_factory.EMBEDDERS_REGISTRY', new_callable=dict)
    def test_raises_for_unknown_engine(self, mock_registry):
        mock_registry.clear()

        with self.assertRaises(MissingEmbedderEngine) as context:
            dispatch_embedder('not_found_engine')

        self.assertIn('not_found_engine', str(context.exception))
