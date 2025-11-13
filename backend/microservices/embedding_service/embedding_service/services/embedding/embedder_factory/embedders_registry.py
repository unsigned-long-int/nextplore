from typing import Dict, Type

from embedding_service.services.embedding.embedders import OpenAIEmbedder, EmbedderBase


EMBEDDERS_REGISTRY: Dict[str, Type[EmbedderBase]] = {
    'open_ai': OpenAIEmbedder
}
