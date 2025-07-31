import asyncio
from typing import Optional, List
from sentence_transformers import SentenceTransformer

from .embedder_base import EmbedderBase


class HuggingFaceEmbedder(EmbedderBase):
    def __init__(self, model_name: str = 'intfloat/e5-large-v2') -> None:
        super().__init__(model_name)
        self.model = SentenceTransformer(model_name)

    async def generate_embedding(self, datastream: str, is_query: Optional[bool] = True) -> List[float]:
        prefix = 'query: ' if is_query else 'passage: '
        formatted = f'{prefix}{datastream}'
        response = await asyncio.to_thread(
            self.model.encode,
            formatted,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return response
