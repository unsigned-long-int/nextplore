from fastapi import Request

from nextplore_orchestrator.clients.integration import IntegrationClient


def get_integration_client(request: Request) -> IntegrationClient:
    return request.app.state.clients.integration_client
