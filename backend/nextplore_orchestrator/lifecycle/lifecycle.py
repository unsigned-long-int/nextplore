from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

from nextplore_shared.logging.setup import setup_logger
from clients.factory import (
    ClientsRegistry,
    ClientsFactory
)
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
    yield
    await registry.close_clients()