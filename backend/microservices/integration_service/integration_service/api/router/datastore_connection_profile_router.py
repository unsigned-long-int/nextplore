import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from nextplore_sdk.encryptor.client.azure_crypto_client import AzureCryptoClient
from svc_integration_contracts.models import DataStoreConnectionProfile

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_backend_connector
from integration_service.cache import CacheService, get_cache_service
from integration_service.database.exceptions import DataStoreGetFailed, SecretsGetFailed
from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.models.secret import SecretType
from integration_service.services.encryption import decrypt_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integration", tags=["ConnectionProfile"])


@router.get(
    "/organizations/{organization_id}/users/{user_id}/datastores/{datastore_id}/connection-profile",
    response_model=DataStoreConnectionProfile,
)
async def get_datastore_connection_profile(
    organization_id: UUID,
    user_id: UUID,
    datastore_id: UUID,
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: CacheService = Depends(get_cache_service),
) -> DataStoreConnectionProfile:
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
        cached = await cache_service.get_datastore_connection_profile(
            user_identity=user_identity, datastore_id=datastore_id
        )
        if cached:
            return cached

        datastore_repo = DataStoreRepository(backend_connector)
        datastore, secrets = await asyncio.gather(
            datastore_repo.get_datastore(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                datastore_id=datastore_id,
            ),
            datastore_repo.get_secrets(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                datastore_id=datastore_id,
            ),
        )
        crypto_client = AzureCryptoClient(datastore.kek_kid)

        response = DataStoreConnectionProfile(
            auth=datastore.auth,
            cloud=datastore.cloud,
            db=datastore.db,
            host=datastore.host,
            database_name=datastore.database_name,
            port=datastore.port,
            warehouse=datastore.warehouse,
            username=decrypt_secret(SecretType.USERNAME, secrets, crypto_client),
            password=decrypt_secret(SecretType.PASSWORD, secrets, crypto_client),
            client_secret=decrypt_secret(
                SecretType.CLIENT_SECRET, secrets, crypto_client
            ),
            aws_external_id=decrypt_secret(
                SecretType.AWS_EXTERNAL_ID, secrets, crypto_client
            ),
            aws_role_arn=decrypt_secret(
                SecretType.AWS_ROLE_ARN, secrets, crypto_client
            ),
            snowflake_private_key=decrypt_secret(
                SecretType.SNOWFLAKE_PRIVATE_KEY, secrets, crypto_client
            ),
            azure_cert_kid=datastore.azure_cert_kid,
            azure_cert_name=datastore.azure_cert_name,
            tenant_id=datastore.tenant_id,
            client_id=datastore.client_id,
            region=datastore.region,
        )

        await cache_service.set_datastore_connection_profile(
            user_identity=user_identity, datastore_id=datastore_id, response=response
        )
        return response
    except DataStoreGetFailed as e:
        logger.error(
            f"Database data store single get request failed with DB error: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except SecretsGetFailed as e:
        logger.error(
            f"Database secret get request failed with DB error: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except Exception as e:
        logger.error(
            f"Unexpected single get data store request error: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
