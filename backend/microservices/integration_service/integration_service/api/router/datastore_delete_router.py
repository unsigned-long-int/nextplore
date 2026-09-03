import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from kafka_messaging.events.integration_service import DataStoreDeleted
from kafka_messaging.message_bus import get_kafka_message_bus
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import CacheService, get_cache_service
from integration_service.database.exceptions import DataStoreDeleteFailed
from integration_service.database.repositories import DataStoreRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integration", tags=["DeleteDataStore"])


@router.delete(
    "/organizations/{organization_id}/users/{user_id}/datastores/{datastore_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_datastore(
    organization_id: UUID,
    user_id: UUID,
    datastore_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service),
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

    datastore_repo = DataStoreRepository(backend_connector)

    try:
        await datastore_repo.delete_datastore(
            datastore_id=datastore_id,
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id,
        )
        await get_kafka_message_bus().publish(
            DataStoreDeleted(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                datastore_id=datastore_id,
            )
        )
        await cache_service.cache.delete_by_prefix(
            user_identity.organization_id, user_identity.user_id
        )

    except DataStoreDeleteFailed as e:
        logger.error(f"Delete data store failed with DB error: {e}.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )

    except Exception as e:
        logger.error(f"Unexpected delete data_store error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
