from fastapi import APIRouter
from .ask_router import router as ask_router
from .introspect_router import router as introspect_router
from .user_profile_router import router as user_profile_router
from .integrations_router import router as integrations_router

api_router = APIRouter()
api_router.include_router(ask_router, prefix='/ask', tags=['Ask'])
api_router.include_router(introspect_router, prefix='/introspect', tags=['Introspect'])
api_router.include_router(user_profile_router, prefix='/me', tags='UserProfile')
api_router.include_router(integrations_router, prefix='/integrations', tags='Integrations')