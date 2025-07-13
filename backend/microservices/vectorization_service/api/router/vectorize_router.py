from fastapi import APIRouter

from shared.contracts.vectorization_service import QueryVectorRequest, VectorResponse
from api.handlers import handle_query_vectorization


router = APIRouter(prefix='/v1/vectorization', tags=['Vectorization'])

@router.post('/vectorize', response_model=VectorResponse)
def vectorize(request: QueryVectorRequest) -> VectorResponse:
    return handle_query_vectorization(request)
