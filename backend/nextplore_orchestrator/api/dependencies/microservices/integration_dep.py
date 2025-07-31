from fastapi import Request
from clients.integration import IntegrationClient


def get_integration_client(request: Request) -> IntegrationClient:
    return request.app.state.clients.integration_client
