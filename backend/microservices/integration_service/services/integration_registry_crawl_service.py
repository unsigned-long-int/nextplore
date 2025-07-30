from typing import List
from uuid import UUID

from utils.catalogs import (
    IntegrationRegistryCatalog,
    IntegrationCatalog
)
from utils.crawlers import crawl_schemas
from utils.filters.logic import Specification
from utils.encryption import decrypt_integration
from database.repositories import IntegrationRepository
from shared.database.connection_builder import build_connection_string, ConnectionMeta
from shared.database.crawler_factory import get_crawler


async def crawl_integration_registry(
        integration_ids: List[UUID], 
        integration_spec: Specification,
        schema_spec: Specification,
        table_spec: Specification
) -> IntegrationRegistryCatalog:
    integration_repo = IntegrationRepository()
    integrations = []

    for integration_id in integration_ids:
        integration_id = integration_id
        integration_meta_candidate = IntegrationCatalog(id=integration_id)
        if not integration_spec.is_satisfied_by(integration_meta_candidate):
            continue
        
        encrypted_integration = await integration_repo.get_integration_by_id(integration_id)
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
        if crawler is None:
            continue
        
        schemas = crawl_schemas(crawler, integration_id, schema_spec, table_spec)
        if schemas:
            integrations.append(IntegrationCatalog(id=integration_id, schemas=schemas))

    return IntegrationRegistryCatalog(integrations=tuple(integrations))
