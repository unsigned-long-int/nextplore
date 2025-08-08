from typing import Dict, Type

from services.embedders import OpenAIEmbedder, EmbedderBase


EMBEDDERS_REGISTRY: Dict[str, Type[EmbedderBase]] = {
    'open_ai': OpenAIEmbedder
}