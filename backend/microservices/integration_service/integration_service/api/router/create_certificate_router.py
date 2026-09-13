import logging
from uuid import UUID

from azure.core.exceptions import AzureError
from fastapi import APIRouter, Depends, HTTPException, status
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from nextplore_sdk.encryptor.cert.cert_generator import CertGenerator
from nextplore_sdk.encryptor.exc.exceptions import AzureCertCreationFailed
from svc_integration_contracts.models import CertCreateRequest

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import CacheService, get_cache_service
from integration_service.database.exceptions import CertCreateFailed
from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.mappers.cert import cert_create_from_dto

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integration", tags=["CreateCertificate"])

UNEXPECTED_ERROR_MESSAGE = "Unexpected server error"
PERSIST_FAILED_MESSAGE = "Failed to persist certificate record"


@router.post(
    "/organizations/{organization_id}/users/{user_id}/datastores/certificates",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def create_certificate(
    organization_id: UUID,
    user_id: UUID,
    payload: CertCreateRequest,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service),
) -> None:
    user_identity = get_current_identity()
    log_ctx = {"org_id": organization_id, "user_id": user_id}

    if (
        organization_id != user_identity.organization_id
        or user_id != user_identity.user_id
    ):
        logger.error("Forbidden request", extra=log_ctx)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"message": "Forbidden"}
        )

    cert_create = cert_create_from_dto(payload)
    purpose = cert_create.purpose or "general"
    cert_name = f"cert-{organization_id!s}-{user_id!s}-{purpose}"
    datastore_repo = DataStoreRepository(backend_connector)

    cert_generator = CertGenerator(cert_name)
    try:
        cert = cert_generator.create_cert(
            key_size=cert_create.key_size,
            validity_in_months=cert_create.validity_in_months,
        )
    except AzureCertCreationFailed as e:
        logger.exception("Create certificate generation failed", extra=log_ctx)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"AKV Error: {e!s}"},
        )
    except Exception:
        logger.exception("Unexpected create certificate error", extra=log_ctx)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": UNEXPECTED_ERROR_MESSAGE},
        )

    try:
        await datastore_repo.create_cert(
            organization_id=organization_id, user_id=user_id, cert=cert
        )
        await cache_service.delete_datastore_cert_profiles(user_identity)
    except CertCreateFailed:
        logger.exception("Create certificate failed with DB error", extra=log_ctx)
        try:
            cert_generator.cert_client.begin_delete_certificate(cert_name)
        except AzureError:
            logger.exception(
                "Failed to roll back orphaned AKV certificate",
                extra={**log_ctx, "cert_name": cert_name},
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": PERSIST_FAILED_MESSAGE},
        )
    except Exception:
        logger.exception("Unexpected create certificate error", extra=log_ctx)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": UNEXPECTED_ERROR_MESSAGE},
        )