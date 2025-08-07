from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from lifecycle import lifespan
from api.middleware import IdentityMiddleware
from api.router import (
    vector_metas_router, 
    vector_stats_router, 
    qdrant_vectors_router,
    vector_profiles_router
)



app = FastAPI(
    title='Vector Handling Service',
    description='Handles vectors retrieval and upserts',
    version = '1.0.0',
    lifespan=lifespan
)

app.add_middleware(IdentityMiddleware)

app.include_router(vector_metas_router)
app.include_router(vector_stats_router)
app.include_router(qdrant_vectors_router)
app.include_router(vector_profiles_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
