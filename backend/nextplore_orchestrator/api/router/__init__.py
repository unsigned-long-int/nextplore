from fastapi import APIRouter
from .ai_queries_router import router as ai_queries_router
from .get_generative_models_router import router as generative_models_router
from .user_profile_router import router as user_profile_router
from .integrations_router import router as integrations_router
from .create_integration_router import router as create_integration_router
from .test_integration_router import router as test_integration_router
from .vector_profiles_router import router as vector_profiles_router
from .user_stats_router import router as user_stats_router
from .update_integration_router import router as update_integration_router
from .delete_integration_router import router as delete_integration_router


api_router = APIRouter()
api_router.include_router(ai_queries_router, prefix='/ai-query', tags=['AIQueryRequest'])
api_router.include_router(generative_models_router, prefix='/ai-generative-models', tags=['GenerativeModels'])
api_router.include_router(user_profile_router, prefix='/me', tags='UserProfile')
api_router.include_router(integrations_router, prefix='/integrations', tags='Integrations')
api_router.include_router(create_integration_router, prefix='/create-integration', tags='CreateIntegration')
api_router.include_router(test_integration_router, prefix='/test-integration', tags='TestIntegration')
api_router.include_router(vector_profiles_router, prefix='/vector-profiles', tags='VectorProfile')
api_router.include_router(user_stats_router, prefix='/user-stats', tags='UserStats')
api_router.include_router(update_integration_router, prefix='/update-integration', tags='UpdateIntegration')
api_router.include_router(delete_integration_router, prefix='/delete-integration', tags='DeleteIntegration')
