from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from llm_inference_service.lifecycle import lifespan
from llm_inference_service.api.router import orm_context_router, models_router
from llm_inference_service.api.middleware import IdentityMiddleware


app = FastAPI(
    title='AI ORM Service',
    description='Provides range of LLM models for fetching ORM context for user query',
    version = '1.0.0',
    lifespan=lifespan
)
app.add_middleware(IdentityMiddleware)
app.include_router(orm_context_router)
app.include_router(models_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
