import os
import httpx

from microservices.vectorization_service.api.models import VectorResponse, QueryVectorRequest


class VectorizationClient:
    def __init__(self, base_url: str = f'http://localhost:{os.getenv('VECTORIZATION_PORT')}') -> None:
        self.base_url = base_url
        self.session = httpx.Client(timeout=5.0)

    def vectorize(self, datastream: str) -> VectorResponse:
        payload = QueryVectorRequest(datastream=datastream)
        response = self.session.post(f'{self.base_url}/vectorize', json=payload)
        response.raise_for_status()
        return VectorResponse(**response.json())
    