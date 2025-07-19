from contextlib import asynccontextmanager
from fastapi import FastAPI

from shared.logging import setup_logger
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationMetaCrawled
from api.handlers import handle_crawl_meta_embedding



@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    get_kafka_message_bus().subscribe(
        event_cls=IntegrationMetaCrawled, 
        handler=handle_crawl_meta_embedding
    )
    yield