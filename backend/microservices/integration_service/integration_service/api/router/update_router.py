import logging
import asyncio
from uuid import UUID
from fastapi import APIRouter, status, HTTPException, Depends

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.database.repositories import IntegrationRepository
from integration_service.database.exceptions import IntegrationUpdateFailed
from integration_service.cache import CacheService, get_cache_service
from integration_service.domain.mappers.integration import integration_update_from_dto
from integration_service.domain.mappers.secret import secrets_from_dto
from integration_service.api.models.integration_update_request import IntegrationUpdateRequest
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['UpdateIntegration'])


@router.patch(
    '/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def update_integration(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    payload: IntegrationUpdateRequest,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> None:
    user_identity = get_current_identity()
    if user_identity.user_id != user_id or user_identity.organization_id != organization_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )
    
    integration_repo = IntegrationRepository(backend_connector)
    try:
        integration_update = integration_update_from_dto(payload)
        secret_version = await integration_repo.get_latest_version(
            integration_id=integration_id,
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id
        )
        secrets = secrets_from_dto(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            integration_id=integration_id,
            integration_request=payload,
            version=secret_version + 1
        )

        await integration_repo.update_integration(
            integration_id=integration_id,
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id,
            integration_update=integration_update,
            secrets=secrets
        )

        await cache_service.cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )
    except IntegrationUpdateFailed as e:
        logger.error(
            f'Update integration failed with DB error {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )

    except Exception as e:
        logger.error(
            f'Unexpected update integration error: {e}',
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
