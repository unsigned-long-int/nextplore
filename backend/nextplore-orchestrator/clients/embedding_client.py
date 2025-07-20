from shared.contracts.embedding_service import EmbeddingResponse, QueryEmbeddingRequest
from .base_client import BaseServiceClient


class EmbeddingClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://embedding_service:8001') -> None:
        super().__init__(base_url)

    async def embed(self, datastream: str) -> EmbeddingResponse:
        payload = QueryEmbeddingRequest(datastream=datastream)
        response = await self.post('/v1/embedding/embed', payload)
        return EmbeddingResponse(**response.json())
    