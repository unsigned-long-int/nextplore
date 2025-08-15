import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from database.exceptions import IntegrationGetFailed
from database.repositories import IntegrationRepository
from api.context import get_current_identity
from api.dependencies import get_connector
from cache import CacheService, get_cache_service
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.integration_service.prepared_integration_get_request import PreparedIntegrationGetRequest
from nextplore_sdk.contracts.integration_service.integration_profile_response import IntegrationProfileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integrations', response_model=List[IntegrationProfileResponse])
async def get_integrations(
    payload: PreparedIntegrationGetRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[IntegrationProfileResponse]:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_integrations(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        
        integration_repo = IntegrationRepository(connector)
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

        await cache_service.set_integrations(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except IntegrationGetFailed as e:
        logger.error(f'Get integration profiles request failed with db error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Get integration profiles failed with unexpected error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
