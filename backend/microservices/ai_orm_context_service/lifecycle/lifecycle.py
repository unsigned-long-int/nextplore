from contextlib import asynccontextmanager
from fastapi import FastAPI

from shared.logging import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    yield
