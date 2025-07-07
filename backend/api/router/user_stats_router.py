from fastapi import APIRouter, Depends
from typing import List

from services.database.repositories import IntegrationRepository, VectorRepository
from services.authentication import get_active_user
from services.identity_service import resolve_user_identity
from api.models import UserStats

router = APIRouter()

@router.get('', response_model=UserStats)
def get_user_stats(user=Depends(get_active_user)) ->  UserStats:
    azure_user_id = user.get('oid')
    azure_tenant_id = user.get('tid')
    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)

    integration_repo = IntegrationRepository()
    vector_repo = VectorRepository()

    integration_ids = integration_repo.get_user_integration_ids(user_identity)
    integrations_number = len(integration_ids)
    vectors_number = vector_repo.get_user_vectors_number(integration_ids)
    return UserStats(
        integrations_number=integrations_number, 
        vectors_number=vectors_number
        )

    

