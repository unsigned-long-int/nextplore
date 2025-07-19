from fastapi import Request
from clients import VectorClient


def get_vector_client(request: Request) -> VectorClient:
    return request.app.state.clients.vector_client
