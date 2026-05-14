from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from vector_service.lifecycle import lifespan
from vector_service.api.middleware import IdentityMiddleware
from vector_service.api.router import (
    meta_router, 
    stats_router, 
    nearest_neighbours_router,
    profiles_router,
    semantic_cache_store_router,
    semantic_cache_lookup_router
)


app = FastAPI(
    title='Vector Handling Service',
    description='Handles vectors retrieval and upserts',
    version = '1.0.0',
    lifespan=lifespan
)

app.add_middleware(IdentityMiddleware)

app.include_router(meta_router)
app.include_router(stats_router)
app.include_router(nearest_neighbours_router)
app.include_router(profiles_router)
app.include_router(semantic_cache_store_router)
app.include_router(semantic_cache_lookup_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
