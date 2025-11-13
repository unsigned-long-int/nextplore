from fastapi import Request

from nextplore_orchestrator.clients.vector import VectorClient


def get_vector_client(request: Request) -> VectorClient:
    return request.app.state.clients.vector_client
