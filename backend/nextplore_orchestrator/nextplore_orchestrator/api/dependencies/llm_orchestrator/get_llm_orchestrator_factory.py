from fastapi import Request

from nextplore_orchestrator.services.query_orchestrator.llm_orchestrator import (
    LlmOrchestratorFactory,
)


def get_llm_orchestrator_factory(request: Request) -> LlmOrchestratorFactory:
    return request.app.state.llm_orchestrator_factory
