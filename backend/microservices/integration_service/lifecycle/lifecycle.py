from contextlib import asynccontextmanager
from fastapi import FastAPI

from shared.logging import setup_logger
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationCreated
from api.handlers import crawl_initial_integration_metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    kafka_message_bus = get_kafka_message_bus()
    await kafka_message_bus.start()
    await kafka_message_bus.subscribe(
        event_cls=IntegrationCreated, handler=crawl_initial_integration_metadata
    )

    yield

    await kafka_message_bus.stop()