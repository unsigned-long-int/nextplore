from typing import List
from fastapi import APIRouter

from database.repositories import IntegrationRepository
from api.context import get_current_identity
from nextplore_shared.contracts.integration_service.prepared_integration_get_request import PreparedIntegrationGetRequest
from nextplore_shared.contracts.integration_service.integration_profile_response import IntegrationProfileResponse
from nextplore_shared.cache.service_caches.integration_cache.cache import integration_service_cache


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integrations', response_model=List[IntegrationProfileResponse])
async def get_integrations(payload: PreparedIntegrationGetRequest) -> List[IntegrationProfileResponse]:
    user_identity = get_current_identity()
    cached = await integration_service_cache.get_integrations(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    
    integration_repo = IntegrationRepository()
    user_integration_profiles = await integration_repo.get_user_integration_profiles(
        user_id=payload.user_id,
        organization_id=payload.organization_id
    )
    response = [
        IntegrationProfileResponse(
            id=integration_profile.id,
            service_type=integration_profile.service_type,
            connection_name=integration_profile.connection_name,
            database_name=integration_profile.database_name,
            auth_method=integration_profile.auth_method,
            autosync_on=integration_profile.autosync_on
        ) for integration_profile in user_integration_profiles
    ]

    await integration_service_cache.set_integrations(
        user_identity=user_identity,
        request=payload,
        response=response
    )
    return response
