from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

from nextplore_sdk.logging.setup import setup_logger
from nextplore_sdk.cache.client.base_redis_client import BaseCache
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_orchestrator.clients.factory import (
    ClientsRegistry,
    ClientsFactory
)
from nextplore_orchestrator.api.dependencies.authentication import JWKSFetcher, TokenVerifier
from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService
from nextplore_orchestrator.cache.identity_cache import IdentityCacheService
from nextplore_orchestrator.cache.jwks_cache import JWKSCacheService
from _version import version, app_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )

    backend_connector = DatabaseBackendConnector()
    backend_connector.init()
    app.state.backend_connector = backend_connector
    
    clients_factory = ClientsFactory()
    registry = ClientsRegistry(
        integration_client=clients_factory.create_integration_client(),
        embedding_client=clients_factory.create_embedding_client(),
        vector_client=clients_factory.create_vector_client(),
        ai_orm_context_client=clients_factory.create_ai_orm_context_client()
    )
    app.state.clients = registry

    engine_manager = EngineManager()
    app.state.engine_manager = engine_manager

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
    await engine_manager.shutdown()
    await backend_connector.dispose()
