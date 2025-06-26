import uuid
from fastapi import APIRouter, Depends

from services.database.dependencies import backend_session_scope
from services.database.models import Organization, User
from services.authentication import get_active_user
from api.models import UserProfile

router = APIRouter()

@router.get('', response_model=UserProfile)
def get_vectors():
    pass