import logging
from fastapi import APIRouter, HTTPException, status, Depends

from nextplore_sdk.contracts.integration_service.integration_stats_request import IntegrationStatsRequest
from nextplore_sdk.contracts.integration_service.integration_stats_response import IntegrationStatsResponse
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from cache import CacheService, get_cache_service
from api.context import get_current_identity
from api.dependencies import get_connector
from database.exceptions import IntegrationGetFailed
from database.repositories import IntegrationRepository


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integration-stats', response_model=IntegrationStatsResponse)
async def get_integration_stats(
    payload: IntegrationStatsRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> IntegrationStatsResponse:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_integration_stats(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached

        integration_repo = IntegrationRepository(connector)

        integration_ids = await integration_repo.get_user_integration_ids(
            user_id=payload.user_id,
            organization_id=payload.organization_id
        )

        response = IntegrationStatsResponse(
            integration_ids=integration_ids,
            integration_count=len(integration_ids)
        )
        await cache_service.set_integration_stats(
            user_identity=user_identity,
            request=payload, 
            response=response
        )
        return response
    except IntegrationGetFailed as e:
        logger.error(f'Get integration stats request failed with db error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Get integration stats failed with unexpected error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )