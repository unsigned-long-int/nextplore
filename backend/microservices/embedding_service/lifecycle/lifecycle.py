from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path

from nextplore_shared.logging.setup import setup_logger
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationMetaCrawled
from api.handlers import handle_crawl_meta_embedding
from _version import app_name, version


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    kafka_message_bus = get_kafka_message_bus()
    await kafka_message_bus.start()
    await kafka_message_bus.subscribe(
        event_cls=IntegrationMetaCrawled, 
        handler=handle_crawl_meta_embedding
    )
    
    yield

    await kafka_message_bus.stop()