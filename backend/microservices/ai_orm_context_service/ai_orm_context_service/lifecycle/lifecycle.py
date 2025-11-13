import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path

from nextplore_sdk.cache.client.base_redis_client import BaseCache
from nextplore_sdk.logging.setup import setup_logger
from ai_orm_context_service.cache import CacheService
from ai_orm_context_service.services.orm_context.models_registry import setup_models_registry
from _version import version, app_name


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    models_registry = setup_models_registry()
    app.state.models_registry = models_registry

    cache = BaseCache(namespace='ai_orm_context_cache_service', version='v1')
    app.state.cache_service = CacheService(cache)

    yield
