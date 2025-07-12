from fastapi import FastAPI

from api.router import filter_router, initial_router


app = FastAPI(
    title='Integration Registry Inspection Service',
    description='Handles crawling of the integration and fetching/upserting metadata',
    version = '1.0.0'
)

app.include_router(filter_router)
app.include_router(initial_router)
