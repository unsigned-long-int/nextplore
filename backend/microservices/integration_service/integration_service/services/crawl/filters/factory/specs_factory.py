from typing import List, Dict, Tuple
from uuid import UUID

from integration_service.services.crawl.filters.specs import (
    IntegrationIdSpec,
    SchemaNameSpec,
    TableNameSpec
)


def create_specs(
        integrations: List[UUID], 
        schemas: Dict[str, List[str]],
        tables: Dict[str, List[str]]
) -> Tuple[IntegrationIdSpec, SchemaNameSpec, TableNameSpec]:
    integration_spec = IntegrationIdSpec(integration_ids=set(integrations))
    schema_spec = SchemaNameSpec(allowed_integration_schemas={UUID(key): set(values) for key, values in schemas.items()})
    table_spec = TableNameSpec(allowed_integration_tables={UUID(key): set(values) for key, values in tables.items()})

    return integration_spec, schema_spec, table_spec
