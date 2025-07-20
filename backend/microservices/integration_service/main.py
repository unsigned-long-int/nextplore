from fastapi import FastAPI

from lifecycle import lifespan
from api.router import (
    crawl_filtered_router,
    create_router,
    delete_router,
    get_router,
    test_router,
    update_router,
    integration_stats_router,
    integration_meta_router
)
from api.middleware import IdentityMiddleware


app = FastAPI(
    title='Integration Registry Inspection Service',
    description='Handles crawling of the integration and fetching/upserting metadata',
    version = '1.0.0',
    lifespan=lifespan
)
app.add_middleware(IdentityMiddleware)

app.include_router(crawl_filtered_router)
app.include_router(create_router)
app.include_router(delete_router)
app.include_router(get_router)
app.include_router(test_router)
app.include_router(update_router)
app.include_router(integration_stats_router)
app.include_router(integration_meta_router)
