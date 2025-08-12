import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
from functools import partial

from nextplore_sdk.logging.setup import setup_logger
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from messaging.message_bus import get_kafka_message_bus
from messaging.events.embedding_service import CrawlMetaEmbedded
from messaging.events.integration_service import IntegrationDeleted
from api.handlers import handle_vector_upsert, handle_vector_delete
from _version import version, app_name

DATABASE_URL = (
            f'postgresql+asyncpg://{os.getenv('DB_USR_VECTOR_SERVICE')}:{os.getenv('DB_PWD_VECTOR_SERVICE')}'
            f'@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}'
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    connector = DatabaseBackendConnector(DATABASE_URL)
    connector.init()
    app.state.connector = connector
    kafka_message_bus = get_kafka_message_bus()
    await kafka_message_bus.start()
    await kafka_message_bus.subscribe(
        event_cls=CrawlMetaEmbedded, handler=partial(handle_vector_upsert, connector=connector)
    )
    await kafka_message_bus.subscribe(
        event_cls=IntegrationDeleted,
        handler=partial(handle_vector_delete, connector=connector)
    )

    yield

    await connector.dispose()
    await kafka_message_bus.stop()
