from typing import Dict, Type

from services.embedders import OpenAIEmbedder, HuggingFaceEmbedder, EmbedderBase


EMBEDDERS_REGISTRY: Dict[str, Type[EmbedderBase]] = {
    'open_ai': OpenAIEmbedder,
    'hugging_face': HuggingFaceEmbedder
}