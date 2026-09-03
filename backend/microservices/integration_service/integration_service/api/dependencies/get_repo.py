from fastapi import Request

from integration_service.database.repositories import DataStoreRepository, LlmRepository


def get_data_stores_integration_repo(request: Request) -> DataStoreRepository:
    return request.app.state.data_store_repo


def get_llm_integration_repo(request: Request) -> LlmRepository:
    return request.app.state.llm_repo
