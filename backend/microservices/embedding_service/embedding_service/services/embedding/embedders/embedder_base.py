from abc import ABC, abstractmethod


class EmbedderBase(ABC):
    def __init__(self, model_name) -> None:
        self.model_name = model_name

    @abstractmethod
    async def generate_embedding(self, datastream: str) -> list[float]:
        pass
