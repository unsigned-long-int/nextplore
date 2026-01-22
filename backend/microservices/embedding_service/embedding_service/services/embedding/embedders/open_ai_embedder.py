import os
import logging
from typing import List

from embedding_service.services.embedding.exceptions import EmbeddingFailed
from nextplore_sdk.open_ai_client_loader.open_ai_client_loader import load_open_ai_client
from .embedder_base import EmbedderBase


logger = logging.getLogger(__name__)


class OpenAIEmbedder(EmbedderBase):
    def __init__(self, model_name: str = 'text-embedding-3-small') -> None:
        super().__init__(model_name)
        self.client = load_open_ai_client(os.getenv('OPENAI_API_KEY'))

    async def generate_embedding(self, datastream: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                input=datastream,
                model=self.model_name
            )
            return response.data[0].embedding
        except Exception as e:
            msg = f'Failed to generate embedding: {e}'
            logger.error(msg, exc_info=True)
            raise EmbeddingFailed(msg) from e
       