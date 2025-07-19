from typing import List
from fastapi import APIRouter

from database.repositories import IntegrationRepository
from shared.contracts.integration_service import (
    PreparedIntegrationGetRequest, 
    IntegrationProfileResponse
)


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integrations', response_model=List[IntegrationProfileResponse])
def get_integrations(payload: PreparedIntegrationGetRequest) -> List[IntegrationProfileResponse]:
    integration_repo = IntegrationRepository()
    user_integration_profiles = integration_repo.get_user_integration_profiles(
        user_id=payload.user_id,
        organization_id=payload.organization_id
    )
    return [
        IntegrationProfileResponse(
            id=integration_profile.id,
            service_type=integration_profile.service_type,
            connection_name=integration_profile.connection_name,
            database_name=integration_profile.database_name,
            auth_method=integration_profile.auth_method,
            autosync_on=integration_profile.autosync_on
        ) for integration_profile in user_integration_profiles
    ]
