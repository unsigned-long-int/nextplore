import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from svc_vector_contracts.models import VectorProfileResponse
from vector_service.api.context import get_current_identity
from vector_service.api.dependencies import get_backend_connector
from vector_service.cache import CacheService, get_cache_service
from vector_service.database.repositories import VectorRepository
from vector_service.database.exceptions import VectorProfilesGetFailed


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/vector', tags=['VectorProfiles'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}/vectors/profiles',
    response_model=List[VectorProfileResponse]
)
async def get_profiles(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[VectorProfileResponse]:
    user_identity = get_current_identity()
    if organization_id != user_identity.organization_id or user_id != user_identity.user_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )

    try:
        cached = await cache_service.get_vector_profiles(
            user_identity=user_identity,
            integration_id=integration_id
        )
        if cached:
            return cached
        
        vector_repo = VectorRepository(backend_connector)

        vector_profiles = await vector_repo.get_profiles(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=integration_id
        )
        response = [
            VectorProfileResponse(
                integration_id=vector_profile.integration_id,
                schema_name=vector_profile.schema_name,
                table_name=vector_profile.table_name,
                table_meta=str(vector_profile.table_meta)
            ) for vector_profile in vector_profiles
        ]
        await cache_service.set_vector_profiles(
            user_identity=user_identity,
            integration_id=integration_id,
            response=response
        )
        return response
    except VectorProfilesGetFailed as e:
        logger.error(
            f'Get vector profiles failed with DB error: {e}.', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )

    except Exception as e:
        logger.error(f'Unexpected get vector profiles error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
