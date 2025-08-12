from fastapi import Request
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector


def get_connector(request: Request) -> DatabaseBackendConnector:
    return request.app.state.connector