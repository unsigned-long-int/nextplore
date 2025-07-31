from typing import Optional 

from services.embedders import EmbedderBase
from .embedders_registry import EMBEDDERS_REGISTRY


class EmbedderEngineNotFound(Exception):
    pass


def dispatch_embedder(engine: Optional[str] = 'open_ai') -> EmbedderBase:
    embedder = EMBEDDERS_REGISTRY.get(engine)
    if embedder is None:
        raise EmbedderEngineNotFound(f'{engine}: not found')
    return embedder
