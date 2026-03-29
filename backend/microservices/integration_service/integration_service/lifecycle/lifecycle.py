import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
from functools import partial

from nextplore_sdk.cache.client.base_redis_client import BaseCache
from nextplore_sdk.logging.setup import setup_logger
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from kafka_messaging.message_bus import get_kafka_message_bus
from kafka_messaging.events.integration_service import DataStoreCreated

from integration_service.cache import CacheService
from integration_service.api.handlers import crawl_initial_datastore_metadata
from integration_service.database.repositories import DataStoreRepository, LlmRepository
from _version import version, app_name

DATABASE_URL = (
            f'postgresql+asyncpg://{os.getenv("DB_USR_INTEGRATION_SERVICE")}:{os.getenv("DB_PWD_INTEGRATION_SERVICE")}'
            f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    backend_connector = DatabaseBackendConnector(DATABASE_URL)
    backend_connector.init()
    app.state.backend_connector = backend_connector

    data_store_repo = DataStoreRepository(backend_connector)
    app.state.data_store_repo = data_store_repo

    llm_repo = LlmRepository(backend_connector)
    app.state.llm_repo = llm_repo


    cache = BaseCache(namespace='integration_service', version='v1')
    app.state.cache_service = CacheService(cache)

    engine_manager = EngineManager()
    app.state.engine_manager = engine_manager

    kafka_message_bus = get_kafka_message_bus()
    await kafka_message_bus.start()
    await kafka_message_bus.subscribe(
        event_cls=DataStoreCreated, handler=partial(
            crawl_initial_datastore_metadata,
            repo=data_store_repo,
            engine_manager=engine_manager
        )
    )

    yield

    await kafka_message_bus.stop()
    await backend_connector.dispose()
    engine_manager.shutdown()
