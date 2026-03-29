from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


from nextplore_orchestrator.lifecycle import lifespan
from nextplore_orchestrator.api.router import (
    ai_queries_router,
    gen_models_router,
    user_profile_router,
    integration_profiles_router,
    create_integration_router,
    test_integration_router,
    vector_profiles_router,
    user_stats_router,
    update_integration_router,
    delete_integration_router,
    cert_profiles_router,
    create_cert_router,
    create_llm_model_router,
    description_enhancement_router,
    user_llm_profiles_router,
    test_user_llm_router
)

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(ai_queries_router)
app.include_router(gen_models_router)
app.include_router(user_profile_router)
app.include_router(integration_profiles_router)
app.include_router(create_integration_router)
app.include_router(test_integration_router)
app.include_router(vector_profiles_router)
app.include_router(user_stats_router)
app.include_router(update_integration_router)
app.include_router(delete_integration_router)
app.include_router(cert_profiles_router)
app.include_router(create_cert_router)
app.include_router(description_enhancement_router)
app.include_router(create_llm_model_router)
app.include_router(user_llm_profiles_router)
app.include_router(test_user_llm_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
