import logging
from uuid import UUID
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.cert_profile import CertProfile
from integration_service.database.repositories import IntegrationRepository
from integration_service.database.exceptions import CertGetFailed
from integration_service.cache import get_cache_service, CacheService
from integration_service.domain.mappers.cert import to_dto_cert_state
from integration_service.domain.exceptions import MissingCertState
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CertProfiles'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/integrations/certificates/profiles',
    response_model=List[CertProfile]
)
async def get_cert_profiles(
    organization_id: UUID,
    user_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[CertProfile]:
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
        cached = await cache_service.get_cert_profiles(
            user_identity=user_identity
        )
        if cached:
            return cached

        integration_repo = IntegrationRepository(backend_connector)
        cert_profiles = await integration_repo.get_cert_profiles(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id
        )
        response = [
            CertProfile(
                id=profile.id,
                state=to_dto_cert_state(profile.state.value),
                cert_kid=profile.cert_kid,
                cert_name=profile.cert_name,
                public_cert_pem=profile.public_cert_pem,
                thumbprint_sha256=profile.thumbprint_sha256,
                not_before=profile.not_before,
                not_after=profile.not_after,
                created_at=profile.created_at,
                assigned_at=profile.assigned_at,
                activated_at=profile.activated_at,
                revoked_at=profile.revoked_at
            )
            for profile in cert_profiles
        ]
        await cache_service.set_cert_profiles(
            user_identity=user_identity,
            response=response
        )
        return response
    except CertGetFailed as e:
        logger.error(
            f'Get certificate profiles failed with DB error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except MissingCertState as e:
        logger.error(
            f'Get certificate profiles failed with mapping error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Mapping error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get certificate profiles failed with unexpected error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
