from fastapi import Request

from nextplore_orchestrator.cache.identity_cache import IdentityCacheService


def get_identity_cache_service(request: Request) -> IdentityCacheService:
    return request.app.state.identity_cache_service
