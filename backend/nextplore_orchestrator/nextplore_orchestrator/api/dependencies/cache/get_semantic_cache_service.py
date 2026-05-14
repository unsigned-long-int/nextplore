from fastapi import Request

from nextplore_orchestrator.cache.semantic_cache_service import SemanticCacheService


def get_semantic_cache_service(request: Request) -> SemanticCacheService:
    return request.app.state.semantic_cache_service
