from fastapi import APIRouter
from .ask_router import router as ask_router
from .introspect_router import router as introspect_router

api_router = APIRouter()
api_router.include_router(ask_router, prefix='/ask', tags=['Ask'])
api_router.include_router(introspect_router, prefix='/introspect', tags=['Introspect'])