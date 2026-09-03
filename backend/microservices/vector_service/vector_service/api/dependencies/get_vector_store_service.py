from fastapi import Request

from vector_service.services.vector_store_service.store.store_service import (
    VectorStoreService,
)


def get_vector_store_service(request: Request) -> VectorStoreService:
    return request.app.state.vector_store_service
