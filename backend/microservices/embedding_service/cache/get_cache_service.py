from fastapi import Request

from .cache_service import CacheService


def get_cache_service(request: Request) -> CacheService:
    return request.app.state.cache_service
