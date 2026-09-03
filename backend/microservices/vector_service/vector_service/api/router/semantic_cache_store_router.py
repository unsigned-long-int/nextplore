import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from svc_vector_contracts.models import SemanticCacheEntry

from vector_service.api.context import get_current_identity
from vector_service.api.dependencies import get_vector_store_service
from vector_service.domain.mappers import semantic_cache_meta_from_dto
from vector_service.services.vector_store_service.exceptions import UpsertVectorDBFailed
from vector_service.services.vector_store_service.store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/vector", tags=["SemanticCacheEntries"])


@router.post(
    "/organizations/{organization_id}/users/{user_id}/semantic-cache",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def store_semantic_cache_entry(
    organization_id: UUID,
    user_id: UUID,
    payload: SemanticCacheEntry,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service),
) -> None:
    user_identity = get_current_identity()

    if (
        organization_id != user_identity.organization_id
        or user_id != user_identity.user_id
    ):
        logger.error(
            "Forbidden request", extra={"org_id": organization_id, "user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"message": "Forbidden"}
        )

    try:
        sem_meta = semantic_cache_meta_from_dto(payload)
        await vector_store_service.store_semantic_cache_entry(
            user_identity=user_identity,
            semantic_cache_meta=sem_meta,
        )
    except UpsertVectorDBFailed as e:
        logger.error(
            f"Upsert semantic cache failed with client error: {e} ",
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Client error: {e!s}"},
        )
    except Exception as e:
        logger.error(
            f"Upsert semantic cache failed with unexpected error: {e!s} ",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
