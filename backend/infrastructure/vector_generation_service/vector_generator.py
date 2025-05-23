from dataclasses import dataclass, field
from typing import Optional, List
from openai import OpenAI


@dataclass
class VectorGenerator:
    client: OpenAI
    datastream: str
    model: Optional[list] = field(default='text-embedding-3-small')

    def generate_vector(self) -> List[float]:
        response = self.client.embeddings.create(
            input=self.datastream,
            model=self.model
        )
        return response.data[0].embedding
