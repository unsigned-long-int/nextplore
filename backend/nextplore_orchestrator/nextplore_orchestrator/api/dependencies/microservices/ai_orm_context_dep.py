from fastapi import Request
from nextplore_orchestrator.clients.ai_orm_context import AIORMContextClient


def get_ai_orm_context_client(request: Request) -> AIORMContextClient:
    return request.app.state.clients.ai_orm_context_client
