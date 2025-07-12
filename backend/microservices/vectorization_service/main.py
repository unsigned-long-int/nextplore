from contextlib import asynccontextmanager
from fastapi import FastAPI

from messaging.message_bus import get_kafka_message_bus
from messaging.events import events
from api.handlers import handle_crawl_meta_vectorization
from api.router import vectorize_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_kafka_message_bus().subscribe(
        event_cls=events.IntegrationMetaCrawled, 
        handler=handle_crawl_meta_vectorization
    )
    yield

app = FastAPI(
    title='Vectorization Service',
    description='Handles vectorizations of datastreams',
    version = '1.0.0',
    lifespan=lifespan
)

app.include_router(vectorize_router)
