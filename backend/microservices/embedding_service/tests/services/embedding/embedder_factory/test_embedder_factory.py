import unittest
from unittest.mock import patch

from embedding_service.services.embedding.embedders import EmbedderBase, OpenAIEmbedder
from embedding_service.services.embedding.embedder_factory import dispatch_embedder
from embedding_service.services.embedding.exceptions import MissingEmbedderEngine


class TestEmbedderFactory(unittest.TestCase):
    def test_dispatches_embedder(self):
        embedder = dispatch_embedder('open_ai')
        self.assertIsNotNone(embedder)
        self.assertTrue(issubclass(embedder, EmbedderBase))

    def test_sets_default_engine(self):
        embedder = dispatch_embedder()
        self.assertIsNotNone(embedder)
        self.assertTrue(issubclass(embedder, EmbedderBase))
        self.assertIs(embedder, OpenAIEmbedder)

    @patch('embedding_service.services.embedding.embedder_factory.embedder_factory.EMBEDDERS_REGISTRY')
    def test_raises_missing_engine(self, embedder_registry_mock):
        embedder_registry_mock.get.return_value = None
        with self.assertRaises(MissingEmbedderEngine) as ctx:
            embedder = dispatch_embedder('open_ai')

        self.assertIn('open_ai: not found', str(ctx.exception))
