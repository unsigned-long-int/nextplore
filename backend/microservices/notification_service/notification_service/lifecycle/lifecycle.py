import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from _version import app_name, version
from fastapi import FastAPI
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from nextplore_sdk.logging.setup import setup_logger

from notification_service.services.notification import NotificationService
from notification_service.services.polling import EmailOutboxPoller

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USR_NOTIFICATION_SERVICE')}:{os.getenv('DB_PWD_NOTIFICATION_SERVICE')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logger(
        service_meta={"version": version, "app_name": app_name},
        config_path=Path(__file__).parents[1] / "config" / "logging-prod.conf",
    )
    backend_connector = DatabaseBackendConnector(DATABASE_URL)
    backend_connector.init()
    notification_svc = NotificationService()
    poller = EmailOutboxPoller(
        db_connector=backend_connector, notification_service=notification_svc
    )

    poller_task: asyncio.Task = asyncio.create_task(poller.start())
    yield

    poller.stop()
    poller_task.cancel()
    await poller_task

    await notification_svc.close()
    await backend_connector.dispose()
