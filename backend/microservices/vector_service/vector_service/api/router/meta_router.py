import json
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from vector_service.api.models.vector_meta_request import VectorMetaRequest
from vector_service.api.models.vector_meta_response import VectorMetaResponse
from vector_service.api.context import get_current_identity
from vector_service.api.dependencies import get_backend_connector
from vector_service.cache import CacheService, get_cache_service
from vector_service.database.repositories import VectorRepository
from vector_service.database.exceptions import VectorGetFailed


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/vector', tags=['VectorMeta'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/integrations/vectors/meta',
    response_model=List[VectorMetaResponse]
)
async def get_meta(
    organization_id: UUID,
    user_id: UUID,
    payload: VectorMetaRequest,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[VectorMetaResponse]:
    try:
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

        cached = await cache_service.get_vector_metas(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        
        vector_repo = VectorRepository(backend_connector)

        vector_metas = await vector_repo.get_vectors(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            vector_ids=payload.vector_ids
        )
        response = [
            VectorMetaResponse(
                integration_id=vector_meta.integration_id,
                schema_name=vector_meta.schema_name,
                table_name=vector_meta.table_name,
                table_meta=json.loads(vector_meta.table_meta)
            ) for vector_meta in vector_metas
        ]
        await cache_service.set_vector_metas(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except VectorGetFailed as e:
        logger.error(
            f'Get vector metas failed with DB error: {e}.', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )

    except Exception as e:
        logger.error(f'Unexpected get vector metas error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
