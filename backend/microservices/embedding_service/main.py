from fastapi import FastAPI

from lifecycle import lifespan
from api.router import embedding_router
from api.middleware import IdentityMiddleware


app = FastAPI(
    title='Embedding Service',
    description='Handles embeddings of datastreams',
    version = '1.0.0',
    lifespan=lifespan
)
app.add_middleware(IdentityMiddleware)

app.include_router(embedding_router)
