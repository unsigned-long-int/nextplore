import logging
from fastapi import APIRouter, HTTPException, status, Depends

from database.repositories import IntegrationRepository
from database.exceptions import IntegrationGetFailed
from utils.encryption import decrypt_integration
from api.context import get_current_identity
from api.dependencies import get_connector
from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_shared.cache.service_caches.integration_cache.cache import integration_service_cache
from nextplore_shared.contracts.integration_service.integration_metadata_request import IntegrationMetadataRequest
from nextplore_shared.contracts.integration_service.integration_metadata_response import IntegrationMetadataResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/get-integration', response_model=IntegrationMetadataResponse)
async def get_integration(
    payload: IntegrationMetadataRequest,
    connector: DatabaseBackendConnector = Depends(get_connector)
) -> IntegrationMetadataResponse:
    try:
        user_identity = get_current_identity()
        cached = await integration_service_cache.get_integration_metadata(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        integration_repo = IntegrationRepository(connector)
        encrypted_integration = await integration_repo.get_integration(
            user_id=payload.user_id,
            organization_id=payload.organization_id,
            integration_id=payload.integration_id
        )

        decrypted_integration = decrypt_integration(encrypted_integration)
        response = IntegrationMetadataResponse(
            service_type=decrypted_integration.service_type,
            auth_method=decrypted_integration.auth_method,
            connection_name=decrypted_integration.connection_name,
            host=decrypted_integration.host,
            port=decrypted_integration.port,
            database_name=decrypted_integration.database_name,
            username=decrypted_integration.username,
            password=decrypted_integration.password,
            kerberos_principal=decrypted_integration.kerberos_principal,
            windows_domain=decrypted_integration.windows_domain,
            extra_options=decrypted_integration.extra_options,
            autosync_on=decrypted_integration.autosync_on
        )
        await integration_service_cache.set_integration_metadata(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except IntegrationGetFailed as e:
        logger.error(f'Database integration get request failed: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Unexpected get integration request error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
 