import asyncio
import os
from dataclasses import dataclass, field 
from typing import Optional, List

from shared.open_ai_client_loader import load_open_ai_client
from .embedder_base import EmbedderBase


 
class OpenAIEmbedder(EmbedderBase):
    def __init__(self, model_name: str = 'text-embedding-3-small') -> None:
        super().__init__(model_name)
        self.client = load_open_ai_client(os.getenv('OPENAI_API_KEY'))

    async def generate_embedding(self, datastream: str, is_query: Optional[bool] = True) -> List[float]:
        response = await asyncio.to_thread(
            self.client.embeddings.create,
            input=datastream,
            model=self.model_name
        )
        return response.data[0].embedding
       