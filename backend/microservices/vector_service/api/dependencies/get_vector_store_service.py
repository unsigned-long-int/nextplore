from fastapi import Request

from services.vector_store_service.store import VectorStoreService

def get_vector_store_service(request: Request) -> VectorStoreService:
    return request.app.state.vector_store_service