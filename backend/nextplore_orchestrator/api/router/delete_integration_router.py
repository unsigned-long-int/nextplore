from httpx import HTTPStatusError
from fastapi import APIRouter, Depends

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from api.dependencies.cache import get_orchestrator_cache_service
from cache.orchestrator_cache import OrchestratorCacheService
from nextplore_sdk.contracts.integration_service.prepared_integration_delete_request import PreparedIntegrationDeleteRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_delete_request import IntegrationDeleteRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_delete_response import IntegrationDeleteResponse


router = APIRouter()

@router.post('')
async def delete_integration(
    integration_delete_request: IntegrationDeleteRequest,
    user_identity = Depends(get_active_user),
    integration_client = Depends(get_integration_client),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
) -> IntegrationDeleteResponse:

    payload = PreparedIntegrationDeleteRequest(
        integration_id=integration_delete_request.id,
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    try:
        await integration_client.delete_integration(payload)
        await cache_service.delete_user_stats(user_identity)
        return IntegrationDeleteResponse(success=True)
    except HTTPStatusError as e:
        return IntegrationDeleteResponse(success=False, message=str(e))
