from fastapi import APIRouter
from .ai_queries_router import router as ai_queries_router
from .user_profile_router import router as user_profile_router
from .integrations_router import router as integrations_router
from .create_integration_router import router as create_integration_router
from .test_integration_router import router as test_integration_router
from .vector_metadata_router import router as vector_metadata_router
from .user_stats_router import router as user_stats_router
from .update_integration_router import router as update_integration_router
from .delete_integration_router import router as delete_integration_router


api_router = APIRouter()
api_router.include_router(ai_queries_router, prefix='/aiquery', tags=['AIQueryRequest'])
api_router.include_router(user_profile_router, prefix='/me', tags='UserProfile')
api_router.include_router(integrations_router, prefix='/integrations', tags='Integrations')
api_router.include_router(create_integration_router, prefix='/createintegration', tags='CreateIntegration')
api_router.include_router(test_integration_router, prefix='/testintegration', tags='TestIntegration')
api_router.include_router(vector_metadata_router, prefix='/vectormetadata', tags='VectorMetadata')
api_router.include_router(user_stats_router, prefix='/userstats', tags='UserStats')
api_router.include_router(update_integration_router, prefix='/updateintegration', tags='UpdateIntegration')
api_router.include_router(delete_integration_router, prefix='/deleteintegration', tags='DeleteIntegration')
