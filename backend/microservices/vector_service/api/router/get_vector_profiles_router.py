import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.vector_service.vector_profile_response import VectorProfileResponse
from nextplore_sdk.contracts.vector_service.vector_profile_request import VectorProfileRequest
from api.context import get_current_identity
from api.dependencies import get_connector
from cache import CacheService, get_cache_service
from database.repositories import VectorRepository
from database.exceptions import VectorProfilesGetFailed


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/vector', tags=['Vector'])

@router.post('/get-vector-profiles', response_model=List[VectorProfileResponse])
async def get_vector_profiles(
    payload: VectorProfileRequest,
    connector: DatabaseBackendConnector = Depends(get_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[VectorProfileResponse]:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_vector_profiles(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        
        vector_repo = VectorRepository(connector)

        vector_profiles = await vector_repo.get_vector_profiles(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=payload.integration_id
        )
        response = [
            VectorProfileResponse(
                integration_id=vector_profile.integration_id,
                schema_name=vector_profile.schema_name,
                table_name=vector_profile.table_name,
                table_meta=json.loads(vector_profile.table_meta)
            ) for vector_profile in vector_profiles
        ]
        await cache_service.set_vector_profiles(
            user_identity=user_identity,
            request=payload,
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
