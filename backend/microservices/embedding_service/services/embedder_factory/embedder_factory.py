from typing import Optional, Type

from services.embedders import EmbedderBase
from services.exceptions import MissingEmbedderEngine
from .embedders_registry import EMBEDDERS_REGISTRY

def dispatch_embedder(engine: Optional[str] = 'open_ai') -> Type[EmbedderBase]:
    embedder = EMBEDDERS_REGISTRY.get(engine)
    if embedder is None:
        raise MissingEmbedderEngine(f'{engine}: not found')
    return embedder
