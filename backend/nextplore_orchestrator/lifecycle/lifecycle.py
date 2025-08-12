from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

from nextplore_sdk.logging.setup import setup_logger
from nextplore_sdk.cache.client.base_redis_client import BaseCache
from clients.factory import (
    ClientsRegistry,
    ClientsFactory
)
from api.dependencies.authentication import JWKSFetcher, TokenVerifier
from cache.orchestrator_cache import OrchestratorCacheService
from cache.identity_cache import IdentityCacheService
from cache.jwks_cache import JWKSCacheService
from _version import version, app_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    
    clients_factory = ClientsFactory()
    registry = ClientsRegistry(
        integration_client=clients_factory.create_integration_client(),
        embedding_client=clients_factory.create_embedding_client(),
        vector_client=clients_factory.create_vector_client(),
        ai_orm_context_client=clients_factory.create_ai_orm_context_client()
    )
    app.state.clients = registry

    jwks_cache_client = BaseCache(namespace='jwks', version='v1')
    jwks_cache = JWKSCacheService(jwks_cache_client)
    jwks_fetcher = JWKSFetcher(jwks_cache=jwks_cache, ttl=600)
    app.state.jwks_fetcher_service = jwks_fetcher

    token_verifier = TokenVerifier(jwks_fetcher)
    app.state.token_verifier = token_verifier

    orchestrator_cache_client = BaseCache(namespace='nextplore_orchestrator', version='v1')
    app.state.orchestrator_cache_service = OrchestratorCacheService(orchestrator_cache_client)

    identity_cache_client = BaseCache(namespace='user_identity', version='v1')
    app.state.identity_cache_service = IdentityCacheService(identity_cache_client)

    yield

    await registry.close_clients()
    await jwks_fetcher.aclose()