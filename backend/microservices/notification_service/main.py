from fastapi import FastAPI
from typing import Dict
from prometheus_fastapi_instrumentator import Instrumentator

from notification_service.lifecycle import lifespan

app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health() -> Dict[str, str]:
    return {'status': 'ok'}


Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
