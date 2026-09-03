import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from svc_integration_contracts.models import CertProfile

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import CacheService, get_cache_service
from integration_service.database.exceptions import CertGetFailed
from integration_service.database.repositories import DataStoreRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integration", tags=["CertProfiles"])


@router.get(
    "/organizations/{organization_id}/users/{user_id}/datastores/certificates/profiles",
    response_model=list[CertProfile],
)
async def get_cert_profiles(
    organization_id: UUID,
    user_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service),
) -> list[CertProfile]:
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
        cached = await cache_service.get_datastore_cert_profiles(
            user_identity=user_identity
        )
        if cached:
            return cached

        data_store_repo = DataStoreRepository(backend_connector)
        cert_profiles = await data_store_repo.get_datastore_cert_profiles(
            organization_id=user_identity.organization_id, user_id=user_identity.user_id
        )
        response = [
            CertProfile(
                id=profile.id,
                state=profile.state,
                cert_kid=profile.cert_kid,
                cert_name=profile.cert_name,
                public_cert_pem=profile.public_cert_pem,
                thumbprint_sha256=profile.thumbprint_sha256,
                not_before=profile.not_before,
                not_after=profile.not_after,
                created_at=profile.created_at,
                assigned_at=profile.assigned_at,
                activated_at=profile.activated_at,
                revoked_at=profile.revoked_at,
            )
            for profile in cert_profiles
        ]
        await cache_service.set_datastore_cert_profiles(
            user_identity=user_identity, response=response
        )
        return response
    except CertGetFailed as e:
        logger.error(
            f"Get certificate profiles failed with DB error: {e!s}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except Exception as e:
        logger.error(
            f"Get certificate profiles failed with unexpected error: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
