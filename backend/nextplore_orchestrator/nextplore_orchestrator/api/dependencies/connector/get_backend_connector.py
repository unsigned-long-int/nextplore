from fastapi import Request

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector


def get_backend_connector(request: Request) -> DatabaseBackendConnector:
    return request.app.state.backend_connector
