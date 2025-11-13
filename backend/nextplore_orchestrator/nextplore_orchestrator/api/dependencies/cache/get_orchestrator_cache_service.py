from fastapi import Request

from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService


def get_orchestrator_cache_service(request: Request) -> OrchestratorCacheService:
    return request.app.state.orchestrator_cache_service
