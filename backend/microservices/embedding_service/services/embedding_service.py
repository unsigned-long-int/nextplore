import os 
from dataclasses import dataclass, field 
from typing import Optional, List
from openai import OpenAI 

from shared.open_ai_client_loader import load_open_ai_client


@dataclass 
class Embedder:
    client: OpenAI
    datastream: str
    model: Optional[str] = field(default='text-embedding-3-small')

    def generate_embedding(self) -> List[float]:
        response = self.client.embeddings.create(
            input=self.datastream,
            model=self.model
        )
        return response.data[0].embedding
    

def embed(datastream: str) -> List[float]:
    embedder = Embedder(
        client=load_open_ai_client(os.getenv('OPENAI_API_KEY')),
        datastream=datastream
    )

    embedding = embedder.generate_embedding()
    return embedding
