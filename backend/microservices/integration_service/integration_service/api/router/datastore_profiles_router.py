import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from svc_integration_contracts.models import DataStoreProfile

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import CacheService, get_cache_service
from integration_service.database.exceptions import DataStoreGetFailed
from integration_service.database.repositories import DataStoreRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integration", tags=["DataStoreProfiles"])


@router.get(
    "/organizations/{organization_id}/users/{user_id}/datastores/profiles",
    response_model=list[DataStoreProfile],
)
async def get_datastore_profiles(
    organization_id: UUID,
    user_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service),
) -> list[DataStoreProfile]:
    user_identity = get_current_identity()
    if (
        user_identity.user_id != user_id
        or user_identity.organization_id != organization_id
    ):
        logger.error(
            "Forbidden request", extra={"org_id": organization_id, "user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"message": "Forbidden"}
        )
    try:
        cached = await cache_service.get_datastore_profiles(user_identity=user_identity)
        if cached:
            return cached

        datastore_repo = DataStoreRepository(backend_connector)
        datastore_profiles = await datastore_repo.get_datastore_profiles(
            user_id=user_identity.user_id, organization_id=user_identity.organization_id
        )
        response = [
            DataStoreProfile(
                id=datastore.id,
                auth=datastore.auth,
                cloud=datastore.cloud,
                db=datastore.db,
                connection_name=datastore.connection_name,
                database_name=datastore.database_name,
                host=datastore.host,
                port=datastore.port,
                autosync_on=datastore.autosync_on,
            )
            for datastore in datastore_profiles
        ]
        await cache_service.set_datastore_profiles(
            user_identity=user_identity, response=response
        )
        return response
    except DataStoreGetFailed as e:
        logger.error(
            f"Get data store profiles request failed with DB error: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except Exception as e:
        logger.error(
            f"Get data store profiles failed with unexpected error: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
