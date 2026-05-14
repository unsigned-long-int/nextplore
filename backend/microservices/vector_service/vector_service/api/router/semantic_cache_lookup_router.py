import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from svc_vector_contracts.models import SemanticCacheLookupResult, SemanticCacheLookupQuery

from vector_service.domain.mappers import refine_filters_from_dto
from vector_service.api.context import get_current_identity
from vector_service.api.dependencies import get_vector_store_service
from vector_service.services.vector_store_service.exceptions import SearchVectorDBFailed
from vector_service.services.vector_store_service.store import VectorStoreService



logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/vector', tags=['SemanticCacheLookup'])

@router.post(
    '/organizations/{organization_id}/users/{user_id}/semantic-cache/lookup',
    response_model=SemanticCacheLookupResult
)
async def lookup_semantic_cache(
    organization_id: UUID,
    user_id: UUID,
    payload: SemanticCacheLookupQuery,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
) -> SemanticCacheLookupResult:
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
        sem_cache_refine_filters = refine_filters_from_dto(payload)
        semantic_match = await vector_store_service.lookup_semantic_cache(
            user_identity=user_identity,
            embedding=payload.embedding,
            refine_filters=sem_cache_refine_filters,
        )

        if semantic_match:
            return SemanticCacheLookupResult(
                hit=True,
                json_payload=semantic_match.json_payload,
            )
        return SemanticCacheLookupResult(
            hit=False
        )
    except SearchVectorDBFailed as e:
        logger.error(
            f'Get semantic cache failed with client error: {e} ',
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Client error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get semantic cache failed with unexpected error: {str(e)} ',
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
