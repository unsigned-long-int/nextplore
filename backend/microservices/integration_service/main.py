from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from integration_service.lifecycle import lifespan
from integration_service.api.router import (
    crawl_router,
    create_router,
    delete_router,
    profiles_router,
    test_router,
    update_router,
    stats_router,
    connection_profile_router,
    cert_profiles_router,
    create_certificate_router
)
from integration_service.api.middleware import IdentityMiddleware


app = FastAPI(
    title='Integration Registry Inspection Service',
    description='Handles crawling of the integration, fetching/upserting metadata and encryption of connections',
    version='1.0.0',
    lifespan=lifespan
)
app.add_middleware(IdentityMiddleware)

app.include_router(crawl_router)
app.include_router(create_router)
app.include_router(delete_router)
app.include_router(profiles_router)
app.include_router(test_router)
app.include_router(update_router)
app.include_router(stats_router)
app.include_router(connection_profile_router)
app.include_router(cert_profiles_router)
app.include_router(create_certificate_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
