import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path

from services.models_registry import setup_models_registry
from nextplore_shared.logging.setup import setup_logger
from _version import version, app_name


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(
        service_meta={'version': version, 'app_name': app_name},
        config_path=Path(__file__).parents[1] / 'config' / 'logging-prod.conf'
    )
    models_registry = setup_models_registry()
    app.state.models_registry = models_registry
    yield
