import httpx

from shared.contracts.vectorization_service import VectorResponse, QueryVectorRequest


class VectorizationClient:
    def __init__(self, base_url: str = f'http://vectorization_service:8001') -> None:
        self.base_url = base_url
        self.session = httpx.Client(timeout=5.0)

    def vectorize(self, datastream: str) -> VectorResponse:
        payload = QueryVectorRequest(datastream=datastream)
        print(f'vectorizing the data: {payload}')
        response = self.session.post(
            f'{self.base_url}/v1/vectorization/vectorize', 
            data=payload.model_dump_json(),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return VectorResponse(**response.json())
    