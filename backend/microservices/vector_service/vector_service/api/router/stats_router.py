import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from svc_vector_contracts.models import VectorIndexStats

from vector_service.api.context import get_current_identity
from vector_service.api.dependencies import get_backend_connector
from vector_service.cache import CacheService, get_cache_service
from vector_service.database.exceptions import VectorCountGetFailed
from vector_service.database.repositories import VectorRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/vector", tags=["VectorStats"])


@router.get(
    "/organizations/{organization_id}/users/{user_id}/stats",
    response_model=VectorIndexStats,
)
async def get_stats(
    organization_id: UUID,
    user_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service),
) -> VectorIndexStats:
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
        cached = await cache_service.get_stats(user_identity=user_identity)
        if cached:
            return cached

        vector_repo = VectorRepository(backend_connector)

        vector_count = await vector_repo.get_vector_count(
            organization_id=organization_id, user_id=user_id
        )
        response = VectorIndexStats(vector_count=vector_count)
        await cache_service.set_stats(user_identity=user_identity, response=response)
        return response
    except VectorCountGetFailed as e:
        logger.error(f"Get vector stats failed with DB error: {e}.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except Exception as e:
        logger.error(f"Unexpected get vector stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
