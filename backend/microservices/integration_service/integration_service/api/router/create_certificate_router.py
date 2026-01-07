import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.cert_create_request import CertCreateRequest
from integration_service.database.repositories import IntegrationRepository
from integration_service.database.exceptions import CertCreateFailed
from integration_service.domain.mappers.cert import cert_create_from_dto
from integration_service.cache import CacheService, get_cache_service
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.encryptor.cert.cert_generator import CertGenerator
from nextplore_sdk.encryptor.exc.exceptions import AzureCertCreationFailed

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CreateCertificate'])


@router.post(
    '/organizations/{organization_id}/users/{user_id}/integrations/certificates',
    status_code=status.HTTP_204_NO_CONTENT
)
async def create_certificate(
    organization_id: UUID,
    user_id: UUID,
    payload: CertCreateRequest,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> None:
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

    cert_create = cert_create_from_dto(payload)
    purpose = cert_create.purpose or 'general'
    cert_name = f'cert-{str(organization_id)}-{str(user_id)}-{purpose}'
    integration_repo = IntegrationRepository(backend_connector)
    try:
        cert_generator = CertGenerator(cert_name)
        cert = cert_generator.create_cert(
            key_size=cert_create.key_size,
            validity_in_months=cert_create.validity_in_months
        )
        await integration_repo.create_cert(
            organization_id=organization_id,
            user_id=user_id,
            cert=cert
        )

        await cache_service.delete_cert_profiles(user_identity)
    except AzureCertCreationFailed as e:
        logger.error(
            f'Create certificate failed in AKV: {str(e)}'
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'AKV Error: {str(e)}'}
        )
    except CertCreateFailed as e:
        logger.error(
            f'Create certificate failed with DB error: {str(e)}',
            exc_info=True
        )
    except Exception as e:
        logger.error(
            f'Unexpected create certificate error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
