from typing import Tuple
from uuid import UUID

from core.database.catalogs import (
    IntegrationRegistryCatalog,
    IntegrationCatalog,
    SchemaCatalog,
    TableCatalog
)
from core.database.filter.logic import (
    Specification
)


def filter_tables(tables: Tuple[TableCatalog], table_spec: Specification) -> Tuple[TableCatalog]:
    return tuple([table for table in tables if table_spec.is_satisfied_by(table)])


def filter_schemas(integration_id: UUID, schemas: Tuple[SchemaCatalog], schema_spec: Specification, table_spec: Specification) -> Tuple[SchemaCatalog]:
    result = []
    for schema in schemas:
        if not schema_spec.is_satisfied_by(schema):
            continue

        filtered_tables = filter_tables(schema.tables, table_spec)
        if filtered_tables:
            result.append(SchemaCatalog(integration_id=integration_id, name=schema.name, tables=filtered_tables))
    
    return tuple(result)


def filter_integrations(integrations: Tuple[IntegrationCatalog], integration_spec: Specification, schema_spec: Specification, table_spec: Specification) -> IntegrationRegistryCatalog:
    result = []
    for integration in integrations:
        if not integration_spec.is_satisfied_by(integration):
            continue

        filtered_schemas = filter_schemas(integration.id, integration.schemas, schema_spec, table_spec)
        if filtered_schemas:
            result.append(IntegrationCatalog(id=integration.id, schemas=filtered_schemas))
    
    return IntegrationRegistryCatalog(integrations=tuple(result))
