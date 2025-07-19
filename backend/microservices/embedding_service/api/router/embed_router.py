from fastapi import APIRouter

from shared.contracts.embedding_service import QueryEmbeddingRequest, EmbeddingResponse
from api.handlers import handle_query_embedding


router = APIRouter(prefix='/v1/embedding', tags=['Embedding'])

@router.post('/embed', response_model=EmbeddingResponse)
def embed(request: QueryEmbeddingRequest) -> EmbeddingResponse:
    return handle_query_embedding(request)
