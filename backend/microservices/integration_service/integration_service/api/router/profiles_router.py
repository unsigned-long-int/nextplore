import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from integration_service.database.exceptions import IntegrationGetFailed
from integration_service.database.repositories import IntegrationRepository
from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.integration_profile import IntegrationProfile
from integration_service.cache import CacheService, get_cache_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['IntegrationProfiles'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/integrations/profiles',
    response_model=List[IntegrationProfile]
)
async def get_profiles(
    organization_id: UUID,
    user_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[IntegrationProfile]:
    user_identity = get_current_identity()
    if user_identity.user_id != user_id or user_identity.organization_id != organization_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )
    try:
        cached = await cache_service.get_profiles(
            user_identity=user_identity
        )
        if cached:
            return cached
        
        integration_repo = IntegrationRepository(backend_connector)
        integration_profiles = await integration_repo.get_integration_profiles(
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id
        )
        response = [
            IntegrationProfile(
                id=integration.id,
                auth=integration.auth,
                cloud=integration.cloud,
                db=integration.db,
                connection_name=integration.connection_name,
                database_name=integration.database_name,
                host=integration.host,
                port=integration.port,
                autosync_on=integration.autosync_on
            ) for integration in integration_profiles
        ]
        await cache_service.set_profiles(
            user_identity=user_identity,
            response=response
        )
        return response
    except IntegrationGetFailed as e:
        logger.error(
            f'Get integration profiles request failed with DB error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get integration profiles failed with unexpected error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
