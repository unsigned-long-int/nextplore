from fastapi import Request

from nextplore_orchestrator.clients.embedding import EmbeddingClient


def get_embedding_client(request: Request) -> EmbeddingClient:
    return request.app.state.clients.embedding_client
