from contextlib import asynccontextmanager
from fastapi import FastAPI

from messaging.message_bus import get_kafka_message_bus
from messaging.events import events
from api.handlers import handle_initial_inspection
from api.router import filter_router, initial_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_kafka_message_bus().subscribe(
        event_cls=events.IntegrationCreated, handler=handle_initial_inspection
    )
    yield

app = FastAPI(
    title='Integration Registry Inspection Service',
    description='Handles crawling of the integration and fetching/upserting metadata',
    version = '1.0.0',
    lifespan=lifespan
)

app.include_router(filter_router)
app.include_router(initial_router)
