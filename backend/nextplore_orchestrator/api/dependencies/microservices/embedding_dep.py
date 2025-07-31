from fastapi import Request
from clients.embedding import EmbeddingClient


def get_embedding_client(request: Request) -> EmbeddingClient:
    return request.app.state.clients.embedding_client
