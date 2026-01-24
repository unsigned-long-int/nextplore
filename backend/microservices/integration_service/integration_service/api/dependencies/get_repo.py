from fastapi import Request

from integration_service.database.repositories import IntegrationRepository


def get_repo(request: Request) -> IntegrationRepository:
    return request.app.state.repo
