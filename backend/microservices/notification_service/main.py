from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from notification_service.lifecycle import lifespan

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
