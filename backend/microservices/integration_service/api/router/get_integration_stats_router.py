from fastapi import APIRouter

from shared.contracts.integration_service import (
    IntegrationStatsRequest, 
    IntegrationStatsResponse
)
from shared.cache.service_caches.integration_cache import integration_service_cache
from api.context import get_current_identity
from database.repositories import IntegrationRepository


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integration-stats', response_model=IntegrationStatsResponse)
async def get_integration_stats(payload: IntegrationStatsRequest) -> IntegrationStatsResponse:
    user_identity = get_current_identity()
    cached = await integration_service_cache.get_integration_stats(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached

    integration_repo = IntegrationRepository()

    integration_ids = integration_repo.get_user_integration_ids(
        user_id=payload.user_id,
        organization_id=payload.organization_id
    )

    response = IntegrationStatsResponse(
        integration_ids=integration_ids,
        integration_count=len(integration_ids)
    )
    await integration_service_cache.set_integration_stats(
        user_identity=user_identity,
        request=payload, 
        response=response
    )
    return response