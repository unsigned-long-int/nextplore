import httpx 

from nextplore_shared.contracts.embedding_service.embedding_response import EmbeddingResponse
from nextplore_shared.contracts.embedding_service.query_embedding_request import QueryEmbeddingRequest
from clients.base import BaseServiceClient
from .exceptions import EmbeddingResponseRemoteError


class EmbeddingClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://embedding_service:8001') -> None:
        super().__init__(base_url)

    async def embed(self, datastream: str) -> EmbeddingResponse:
        try:
            payload = QueryEmbeddingRequest(datastream=datastream)
            response = await self.post('/v1/embedding/embed', payload)
            return EmbeddingResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Query embedding response failed')
                    raise EmbeddingResponseRemoteError(message)
                except Exception:
                    raise EmbeddingResponseRemoteError('Embedding response failed and error response could not be parsed')
            raise

    