import os
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

from _version import app_name, version
from fastapi import FastAPI
from kafka_messaging.events.embedding_service import CrawlMetaEmbedded
from kafka_messaging.events.integration_service import DataStoreDeleted
from kafka_messaging.message_bus import get_kafka_message_bus
from nextplore_sdk.cache.client.base_redis_client import BaseCache
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from nextplore_sdk.logging.setup import setup_logger

from vector_service.api.handlers import handle_vector_delete, handle_vector_upsert
from vector_service.cache import CacheService
from vector_service.services.vector_store_service.clients import QDrantStoreClient
from vector_service.services.vector_store_service.store import VectorStoreService

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USR_VECTOR_SERVICE')}:{os.getenv('DB_PWD_VECTOR_SERVICE')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={"version": version, "app_name": app_name},
        config_path=Path(__file__).parents[1] / "config" / "logging-prod.conf",
    )
    backend_connector = DatabaseBackendConnector(DATABASE_URL)
    backend_connector.init()
    app.state.backend_connector = backend_connector

    cache = BaseCache(namespace="vector_service", version="v1")
    vector_cache_service = CacheService(cache)
    app.state.cache_service = vector_cache_service

    qdrant_store_client = QDrantStoreClient(
        cluster_host=os.getenv("QDRANT_CLUSTER_HOST"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    vector_store_service = VectorStoreService(qdrant_store_client)
    app.state.vector_store_service = vector_store_service

    kafka_message_bus = get_kafka_message_bus()
    await kafka_message_bus.start()
    await kafka_message_bus.subscribe(
        event_cls=CrawlMetaEmbedded,
        handler=partial(
            handle_vector_upsert,
            backend_connector=backend_connector,
            cache_service=vector_cache_service,
            vector_store_service=vector_store_service,
        ),
    )
    await kafka_message_bus.subscribe(
        event_cls=DataStoreDeleted,
        handler=partial(
            handle_vector_delete,
            backend_connector=backend_connector,
            cache_service=vector_cache_service,
            vector_store_service=vector_store_service,
        ),
    )

    yield

    await backend_connector.dispose()
    await kafka_message_bus.stop()
    await vector_store_service.aclose()
