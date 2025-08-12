import logging
from typing import List
from uuid import UUID
from sqlalchemy.exc import OperationalError

from utils.catalogs import (
    IntegrationRegistryCatalog,
    IntegrationCatalog
)
from utils.crawlers import crawl_schemas
from utils.filters.logic import Specification
from utils.encryption import decrypt_integration
from database.repositories import IntegrationRepository
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.database.sql_connection_service.session_starter import ConnectionFailed
from nextplore_sdk.database.connection_builder.connection_meta import ConnectionMeta
from nextplore_sdk.database.connection_builder.database_connection_builder import build_connection_string
from nextplore_sdk.database.crawler_factory.create_crawler import get_crawler


logger = logging.getLogger(__name__)

class CrawlIntegrationsFailed(Exception):
    def __init__(self, message: str, failed_ids: list = None) -> None:
        self.message = message
        self.failed_ids = failed_ids or []
        super().__init__(message)


async def crawl_integration_registry(
    connector: DatabaseBackendConnector,
    user_id: UUID,
    organization_id: UUID,
    integration_ids: List[UUID], 
    integration_spec: Specification,
    schema_spec: Specification,
    table_spec: Specification
) -> IntegrationRegistryCatalog:
    integration_repo = IntegrationRepository(connector)
    integrations = []

    for integration_id in integration_ids:
        try:
            integration_meta_candidate = IntegrationCatalog(id=integration_id)
            if not integration_spec.is_satisfied_by(integration_meta_candidate):
                logger.info(f'Integration {integration_id} is not satisfied by spec. Skipping.')
                continue
            
            encrypted_integration = await integration_repo.get_integration_by_id(
                organization_id=organization_id,
                user_id=user_id,
                integration_id=integration_id
            )
            decrypted_integration = decrypt_integration(encrypted_integration)
            connection_meta = ConnectionMeta(
                service_type=decrypted_integration.service_type,
                auth_method=decrypted_integration.auth_method,
                host=decrypted_integration.host,
                port=decrypted_integration.port,
                database_name=decrypted_integration.database_name,
                username=decrypted_integration.username,
                password=decrypted_integration.password,
                kerberos_principal=decrypted_integration.kerberos_principal,
                windows_domain=decrypted_integration.windows_domain,
                extra_options=decrypted_integration.extra_options
            )
            connection_string = build_connection_string(connection_meta)
            crawler = get_crawler(connection_string)        
            schemas = crawl_schemas(crawler, integration_id, schema_spec, table_spec)
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
