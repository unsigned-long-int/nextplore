import logging
import asyncio
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from svc_integration_contracts.models import IntegrationConnectionProfile
from nextplore_sdk.encryptor.client.azure_crypto_client import AzureCryptoClient
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector

from integration_service.database.repositories import IntegrationRepository
from integration_service.database.exceptions import (
    IntegrationGetFailed,
    SecretsGetFailed
)
from integration_service.cache import CacheService, get_cache_service
from integration_service.api.context import get_current_identity
from integration_service.services.encryption import decrypt_secret
from integration_service.api.dependencies import get_backend_connector
from integration_service.domain.models.secret import SecretType

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['ConnectionProfile'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/integrations/{integration_id}/connection-profile',
    response_model=IntegrationConnectionProfile
)
async def get_connection_profile(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service)
) -> IntegrationConnectionProfile:
    
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
        cached = await cache_service.get_connection_profile(
            user_identity=user_identity,
            integration_id=integration_id
        )
        if cached:
            return cached
        
        integration_repo = IntegrationRepository(backend_connector)
        integration, secrets = await asyncio.gather(
            integration_repo.get_integration(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=integration_id
            ),
            integration_repo.get_secrets(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=integration_id
            )
        )
        crypto_client = AzureCryptoClient(integration.kek_kid)

        response = IntegrationConnectionProfile(
            auth=integration.auth,
            cloud=integration.cloud,
            db=integration.db,
            host=integration.host,
            database_name=integration.database_name,
            port=integration.port,
            warehouse=integration.warehouse,
            username=decrypt_secret(SecretType.USERNAME, secrets, crypto_client),
            password=decrypt_secret(SecretType.PASSWORD, secrets, crypto_client),
            client_secret=decrypt_secret(SecretType.SECRET, secrets, crypto_client),
            aws_external_id=decrypt_secret(SecretType.AWS_EXTERNAL_ID, secrets, crypto_client),
            aws_role_arn=decrypt_secret(SecretType.AWS_ROLE_ARN, secrets, crypto_client),
            snowflake_private_key=decrypt_secret(SecretType.SNOWFLAKE_PRIVATE_KEY, secrets, crypto_client),
            azure_cert_kid=integration.azure_cert_kid,
            azure_cert_name=integration.azure_cert_name,
            tenant_id=integration.tenant_id,
            client_id=integration.client_id,
            region=integration.region
        )

        await cache_service.set_connection_profile(
            user_identity=user_identity,
            integration_id=integration_id,
            response=response
        )
        return response
    except IntegrationGetFailed as e:
        logger.error(
            f'Database integration single get request failed with DB error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except SecretsGetFailed as e:
        logger.error(
            f'Database secret get request failed with DB error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(f'Unexpected single get integration request error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
 