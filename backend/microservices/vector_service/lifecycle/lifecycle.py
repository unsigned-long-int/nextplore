from contextlib import asynccontextmanager
from fastapi import FastAPI

from shared.logging import setup_logger
from messaging.message_bus import get_kafka_message_bus
from messaging.events.embedding_service import CrawlMetaEmbedded
from api.handlers import handle_vector_upsert


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    get_kafka_message_bus().subscribe(
        event_cls=CrawlMetaEmbedded, handler=handle_vector_upsert
    )
    yield