from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path

from nextplore_shared.logging.setup import setup_logger
from messaging.message_bus import get_kafka_message_bus
from messaging.events.embedding_service import CrawlMetaEmbedded
from messaging.events.integration_service import IntegrationDeleted
from api.handlers import handle_vector_upsert, handle_vector_delete
from _version import version, app_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    kafka_message_bus = get_kafka_message_bus()
    await kafka_message_bus.start()
    await kafka_message_bus.subscribe(
        event_cls=CrawlMetaEmbedded, handler=handle_vector_upsert
    )
    await kafka_message_bus.subscribe(
        event_cls=IntegrationDeleted,
        handler=handle_vector_delete
    )

    yield

    await kafka_message_bus.stop()
