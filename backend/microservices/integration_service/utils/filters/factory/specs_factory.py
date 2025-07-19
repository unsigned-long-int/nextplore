from typing import List, Dict, Tuple
from uuid import UUID

from utils.filters.specs import (
    IntegrationIdSpec,
    SchemaNameSpec,
    TableNameSpec
)


def create_specs(
        integrations: List[UUID], 
        schemas: Dict[UUID, List[str]], 
        tables: Dict[UUID, List[str]]
) -> Tuple[IntegrationIdSpec, SchemaNameSpec, TableNameSpec]:
    integration_spec = IntegrationIdSpec(integration_ids={integration for integration in integrations})
    schema_spec = SchemaNameSpec(allowed_integration_schemas={key: set(values) for key, values in schemas.items()})
    table_spec = TableNameSpec(allowed_integration_tables={key: set(values) for key, values in tables.items()})

    return integration_spec, schema_spec, table_spec
