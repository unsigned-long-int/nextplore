from fastapi import Request

from cache.orchestrator_cache.orchestrator_cache_service import OrchestratorCacheService


def get_orchestrator_cache_service(request: Request) -> OrchestratorCacheService:
    return request.app.state.orchestrator_cache_service
