import logging
import asyncio
import time
from typing import List
from uuid import UUID
from sqlalchemy.exc import OperationalError
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile
from nextplore_sdk.database.connection_maker.exc.exceptions import ConnectionFailed
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.connection_maker.mappers.to_domain_db import to_domain_db
from nextplore_sdk.database.connection_maker.mappers.to_domain_auth import to_domain_auth
from nextplore_sdk.database.connection_maker.mappers.to_domain_cloud import to_domain_cloud
from nextplore_sdk.encryptor.client.azure_crypto_client import AzureCryptoClient


from integration_service.services.crawl.catalogs import (
    IntegrationRegistryCatalog,
    IntegrationCatalog
)
from integration_service.services.crawl.catalog_builder.build_schemas_catalog import build_schemas_catalog
from integration_service.services.crawl.exceptions import CrawlIntegrationsFailed
from integration_service.services.crawl.filters.logic import Specification
from integration_service.domain.models.secret import SecretType
from integration_service.services.encryption import decrypt_secret
from integration_service.database.repositories import IntegrationRepository


logger = logging.getLogger(__name__)


async def build_integrations_registry_catalog(
        backend_connector: DatabaseBackendConnector,
        engine_manager: EngineManager,
        user_id: UUID,
        organization_id: UUID,
        integration_ids: List[UUID],
        integration_spec: Specification,
        schema_spec: Specification,
        table_spec: Specification
) -> IntegrationRegistryCatalog:
    integration_repo = IntegrationRepository(backend_connector)
    integrations = []

    for integration_id in integration_ids:
        try:
            integration_meta_candidate = IntegrationCatalog(id=integration_id)
            if not integration_spec.is_satisfied_by(integration_meta_candidate):
                logger.info(f'Integration {integration_id} is not satisfied by spec. Skipping.')
                continue

            integration, secrets = await asyncio.gather(
                integration_repo.get_integration_by_id(
                    organization_id=organization_id,
                    user_id=user_id,
                    integration_id=integration_id
                ),
                integration_repo.get_secrets(
                    organization_id=organization_id,
                    user_id=user_id,
                    integration_id=integration_id
                )
            )
            crypto_client = AzureCryptoClient(integration.kek_kid)

            connection_profile = ConnectionProfile(
                cloud=to_domain_cloud(integration.cloud.value),
                auth=to_domain_auth(integration.auth.value),
                db=to_domain_db(integration.db.value),
                database=integration.database_name,
                port=integration.port,
                host=integration.host,
                warehouse=integration.warehouse,
                username=decrypt_secret(SecretType.USERNAME, secrets, crypto_client),
                password=decrypt_secret(SecretType.PASSWORD, secrets, crypto_client),
                client_secret=decrypt_secret(SecretType.CLIENT_SECRET, secrets, crypto_client),
                aws_external_id=decrypt_secret(SecretType.AWS_EXTERNAL_ID, secrets, crypto_client),
                aws_role_arn=decrypt_secret(SecretType.AWS_ROLE_ARN, secrets, crypto_client),
                azure_cert_kid=integration.azure_cert_kid,
                tenant_id=integration.tenant_id,
                client_id=integration.client_id,
                snowflake_private_key=decrypt_secret(SecretType.SNOWFLAKE_PRIVATE_KEY, secrets, crypto_client),
                region=integration.region
            )
            engine = await engine_manager.acquire_engine(connection_profile)
            start = time.monotonic()
            schemas = await asyncio.to_thread(
                build_schemas_catalog,
                engine,
                integration_id,
                schema_spec,
                table_spec
            )
            elapsed = time.monotonic() - start
            logger.info(f'Crawled integration {integration_id} in {elapsed:.2f} seconds (schemas={len(schemas)})')
            if schemas:
                integrations.append(IntegrationCatalog(id=integration_id, schemas=schemas))
        except ConnectionFailed as e:
            logger.warning(f'Integration {integration_id} Connection failed: {e}')
        except OperationalError as e:
            logger.warning(f'Integration {integration_id} SQL operation failed: {e}')
        except Exception as e:
            logger.exception(f'Integration {integration_id} Unexpected error: {type(e).__name__}: {e}')

    if not integrations:
        raise CrawlIntegrationsFailed(
            message=f'None of the {len(integration_ids)} integrations were successfully crawled.',
            failed_ids=integration_ids
        )
    return IntegrationRegistryCatalog(integrations=tuple(integrations))

