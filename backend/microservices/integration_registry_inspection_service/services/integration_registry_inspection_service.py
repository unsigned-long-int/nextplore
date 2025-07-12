from typing import List
from uuid import UUID

from utils.catalogs import (
    IntegrationRegistryCatalog,
    IntegrationCatalog
)
from utils.inspectors import inspect_schemas
from utils.filters.logic import Specification
from shared.database.crawler import get_crawler


def inspect_integration_registry(
        integration_ids: List[UUID], 
        integration_spec: Specification,
        schema_spec: Specification,
        table_spec: Specification
) -> IntegrationRegistryCatalog:
    integrations = []

    for integration_id in integration_ids:
        integration_id = UUID(integration_id)
        integration_meta_candidate = IntegrationCatalog(id=integration_id)
        print(f'integration is satisfied: {integration_spec.is_satisfied_by(integration_meta_candidate)}')
        if not integration_spec.is_satisfied_by(integration_meta_candidate):
            continue
        
        inspector = get_crawler(integration_id)
        if inspector is None:
            continue
        
        schemas = inspect_schemas(inspector, integration_id, schema_spec, table_spec)
        if schemas:
            integrations.append(IntegrationCatalog(id=integration_id, schemas=schemas))

    return IntegrationRegistryCatalog(integrations=tuple(integrations))
