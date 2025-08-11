from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

from nextplore_shared.logging.setup import setup_logger
from clients.factory import (
    ClientsRegistry,
    ClientsFactory
)
from api.dependencies.authentication import JWKSFetcher, TokenVerifier
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
    jwks_fetcher = JWKSFetcher(ttl=600)
    token_verifier = TokenVerifier(jwks_fetcher)

    app.state.clients = registry
    app.state.jwks_fetcher_service = jwks_fetcher
    app.state.token_verifier = token_verifier
    yield
    await registry.close_clients()
    await jwks_fetcher.aclose()