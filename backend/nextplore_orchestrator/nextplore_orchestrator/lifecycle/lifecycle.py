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
from nextplore_orchestrator.services.model_gateway import ModelGateway
from nextplore_orchestrator.services.query_orchestrator.llm_orchestrator import SimpleLlmOrchestrator, \
    ExpandedLlmOrchestrator, LlmOrchestratorFactory
from nextplore_orchestrator.services.query_orchestrator.query_executor import QueryExecutor
from nextplore_orchestrator.services.rag import RagPipeline
from nextplore_orchestrator.services.vector_searcher import VectorSearcher


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
        llm_inference_client=clients_factory.create_llm_inference_client()
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

    vector_searcher = VectorSearcher(
        embedding_client=registry.embedding_client,
        vector_client=registry.vector_client
    )
    model_gateway = ModelGateway(
        llm_inference_client=registry.llm_inference_client,
    )
    query_executor = QueryExecutor(
        integration_client=registry.integration_client,
        engine_manager=engine_manager,
    )
    rag_pipeline = RagPipeline(
        vector_search=vector_searcher,
        model_gateway=model_gateway,
    )

    simple_llm_orchestrator = SimpleLlmOrchestrator(
        vector_search=vector_searcher,
        model_gateway=model_gateway,
        query_executor=query_executor,
    )
    expanded_llm_orchestrator = ExpandedLlmOrchestrator(
        model_gateway=model_gateway,
        query_executor=query_executor,
        rag_pipeline=rag_pipeline,
    )
    app.state.llm_orchestrator_factory = LlmOrchestratorFactory(
        simple_llm_orchestrator=simple_llm_orchestrator,
        expanded_llm_orchestrator=expanded_llm_orchestrator,
    )

    yield

    await registry.close_clients()
    await jwks_fetcher.aclose()
    await backend_connector.dispose()
    engine_manager.shutdown()
