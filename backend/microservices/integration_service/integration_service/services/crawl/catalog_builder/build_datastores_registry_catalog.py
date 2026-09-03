import asyncio
import logging
import time
from uuid import UUID

from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.connection_maker.exc.exceptions import ConnectionFailed
from nextplore_sdk.database.connection_maker.mappers.to_domain_auth import (
    to_domain_auth,
)
from nextplore_sdk.database.connection_maker.mappers.to_domain_cloud import (
    to_domain_cloud,
)
from nextplore_sdk.database.connection_maker.mappers.to_domain_db import to_domain_db
from nextplore_sdk.database.connection_maker.models.connection_profile import (
    ConnectionProfile,
)
from nextplore_sdk.encryptor.client.azure_crypto_client import AzureCryptoClient
from sqlalchemy.exc import OperationalError

from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.models.secret import SecretType
from integration_service.services.crawl.catalog_builder.build_schemas_catalog import (
    build_schemas_catalog,
)
from integration_service.services.crawl.catalogs import (
    DataStoreCatalog,
    DataStoreRegistryCatalog,
)
from integration_service.services.crawl.exceptions import CrawlDataStoresFailed
from integration_service.services.crawl.filters.logic import Specification
from integration_service.services.encryption import decrypt_secret

logger = logging.getLogger(__name__)


async def build_datastores_registry_catalog(
    repo: DataStoreRepository,
    engine_manager: EngineManager,
    user_id: UUID,
    organization_id: UUID,
    datastore_ids: list[UUID],
    datastore_spec: Specification,
    schema_spec: Specification,
    table_spec: Specification,
) -> DataStoreRegistryCatalog:
    datastores = []

    for datastore_id in datastore_ids:
        try:
            datastore_meta_candidate = DataStoreCatalog(id=datastore_id)
            if not datastore_spec.is_satisfied_by(datastore_meta_candidate):
                logger.info(
                    f"Data store {datastore_id} is not satisfied by spec. Skipping."
                )
                continue

            datastore, secrets = await asyncio.gather(
                repo.get_datastore_by_id(
                    organization_id=organization_id,
                    user_id=user_id,
                    datastore_id=datastore_id,
                ),
                repo.get_secrets(
                    organization_id=organization_id,
                    user_id=user_id,
                    datastore_id=datastore_id,
                ),
            )
            crypto_client = AzureCryptoClient(datastore.kek_kid)

            connection_profile = ConnectionProfile(
                cloud=to_domain_cloud(datastore.cloud.value),
                auth=to_domain_auth(datastore.auth.value),
                db=to_domain_db(datastore.db.value),
                database=datastore.database_name,
                port=datastore.port,
                host=datastore.host,
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
                azure_cert_kid=datastore.azure_cert_kid,
                tenant_id=datastore.tenant_id,
                client_id=datastore.client_id,
                snowflake_private_key=decrypt_secret(
                    SecretType.SNOWFLAKE_PRIVATE_KEY, secrets, crypto_client
                ),
                region=datastore.region,
            )
            engine = await engine_manager.acquire_engine(connection_profile)
            start = time.monotonic()
            schemas = await asyncio.to_thread(
                build_schemas_catalog, engine, datastore_id, schema_spec, table_spec
            )
            elapsed = time.monotonic() - start
            logger.info(
                f"Crawled datastore {datastore_id} in {elapsed:.2f} seconds (schemas={len(schemas)})"
            )
            if schemas:
                datastores.append(DataStoreCatalog(id=datastore_id, schemas=schemas))
        except ConnectionFailed as e:
            logger.warning(f"Data store {datastore_id} Connection failed: {e!s}")
        except OperationalError as e:
            logger.warning(f"Data store {datastore_id} SQL operation failed: {e!s}")
        except Exception as e:
            logger.exception(
                f"Data store {datastore_id} Unexpected error: {type(e).__name__}: {e}"
            )

    if not datastores:
        raise CrawlDataStoresFailed(
            message=f"None of the {len(datastore_ids)} data stores were successfully crawled.",
            failed_ids=datastore_ids,
        )
    return DataStoreRegistryCatalog(datastores=tuple(datastores))
