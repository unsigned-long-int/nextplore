from fastapi import FastAPI
from contextlib import asynccontextmanager

from shared.logging import setup_logger
from clients import (
    ClientsRegistry,
    ClientsFactory
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    
    clients_factory = ClientsFactory()
    registry = ClientsRegistry(
        integration_client=clients_factory.create_integration_client(),
        embedding_client=clients_factory.create_embedding_client(),
        vector_client=clients_factory.create_vector_client()
    )

    app.state.clients = registry
    yield
    await registry.close_clients()