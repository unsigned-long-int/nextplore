from contextlib import asynccontextmanager
from fastapi import FastAPI

from lifecycle import lifespan
from api.router import vector_metas_router, vector_stats_router



app = FastAPI(
    title='Vector Handling Service',
    description='Handles vectors retrieval and upserts',
    version = '1.0.0',
    lifespan=lifespan
)

app.include_router(vector_metas_router)
app.include_router(vector_stats_router)
