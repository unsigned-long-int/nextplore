from abc import ABC, abstractmethod
from typing import List, Optional


class EmbedderBase(ABC):
    def __init__(self, model_name) -> None:
        self.model_name = model_name

    @abstractmethod
    async def generate_embedding(self, datastream: str, is_query: Optional[bool] = True) -> List[float]:
        pass
    