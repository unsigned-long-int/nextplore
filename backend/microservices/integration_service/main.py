from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from integration_service.lifecycle import lifespan
from integration_service.api.router import (
    datastore_crawl_router,
    datastore_create_router,
    datastore_delete_router,
    datastore_profiles_router,
    datastore_test_router,
    datastore_update_router,
    datastore_stats_router,
    datastore_connection_profile_router,
    cert_profiles_router,
    create_certificate_router,
    user_llm_create_router,
    user_llm_profiles_router,
)
from integration_service.api.middleware import IdentityMiddleware


app = FastAPI(
    title='Integration Registry Service',
    description='''
        Handles secure integration of data stores and user custom llms. 
        Responsible for encrypting connection credentials and crawling data stores.''',
    version='1.0.0',
    lifespan=lifespan
)
app.add_middleware(IdentityMiddleware)

app.include_router(datastore_crawl_router)
app.include_router(datastore_create_router)
app.include_router(datastore_delete_router)
app.include_router(datastore_profiles_router)
app.include_router(datastore_test_router)
app.include_router(datastore_update_router)
app.include_router(datastore_stats_router)
app.include_router(datastore_connection_profile_router)
app.include_router(cert_profiles_router)
app.include_router(create_certificate_router)
app.include_router(user_llm_create_router)
app.include_router(user_llm_profiles_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
