import os 
from dataclasses import dataclass, field 
from typing import Optional, List
from openai import OpenAI 

from shared.open_ai_client_loader import load_open_ai_client


@dataclass 
class Vectorizer:
    client: OpenAI
    datastream: str
    model: Optional[str] = field(default='text-embedding-3-small')

    def generate_vector(self) -> List[float]:
        response = self.client.embeddings.create(
            input=self.datastream,
            model=self.model
        )
        return response.data[0].embedding
    

def vectorize(datastream: str) -> List[float]:
    vectorizer = Vectorizer(
        client=load_open_ai_client(os.getenv('OPENAI_API_KEY')),
        datastream=datastream
    )

    vector = vectorizer.generate_vector()
    return vector
