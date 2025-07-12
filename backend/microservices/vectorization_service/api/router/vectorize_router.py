from fastapi import APIRouter

from api.models import QueryVectorRequest, VectorResponse
from api.handlers import handle_vectorization


router = APIRouter(prefix='/v1/vectorization', tags=['Vectorization'])

@router.post('/vectorize', response_model=QueryVectorRequest)
def vectorize(request: QueryVectorRequest) -> VectorResponse:
    return handle_vectorization(request)
