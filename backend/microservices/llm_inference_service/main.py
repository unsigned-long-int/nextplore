from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from llm_inference_service.api.middleware import IdentityMiddleware
from llm_inference_service.api.router import (
    chat_router,
    models_router,
    multi_query_router,
    orm_context_router,
    user_llm_test_router,
)
from llm_inference_service.lifecycle import lifespan

app = FastAPI(
    title="LLM Inference Service",
    description="Provides range of LLM models for fetching RAG ORM context for user query",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(IdentityMiddleware)
app.include_router(orm_context_router)
app.include_router(models_router)
app.include_router(multi_query_router)
app.include_router(chat_router)
app.include_router(user_llm_test_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
