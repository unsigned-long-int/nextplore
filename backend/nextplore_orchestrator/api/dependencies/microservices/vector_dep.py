from fastapi import Request
from clients.vector import VectorClient


def get_vector_client(request: Request) -> VectorClient:
    return request.app.state.clients.vector_client
