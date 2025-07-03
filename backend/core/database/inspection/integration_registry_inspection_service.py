import logging
from uuid import UUID
from sqlalchemy import quoted_name
from sqlalchemy.engine.reflection import Inspector
from typing import List, Tuple



from core.database.catalogs import (
    IntegrationRegistryCatalog,
    IntegrationCatalog,
    SchemaCatalog,
    TableCatalog
)
from core.database.filter.logic import Specification
from .get_inspector import get_inspector


logger = logging.getLogger(__name__)


def _inspect_tables(inspector: Inspector, integration_id: UUID, schema_name: str, table_spec: Specification) -> Tuple[TableCatalog]:
    table_names = inspector.get_table_names(schema=quoted_name(schema_name, quote=True))
    tables = []

    for table_name in table_names:
        table_candidate = TableCatalog(integration_id=integration_id, name=table_name)
        if not table_spec.is_satisfied_by(table_candidate):
            continue
        try:
            table = TableCatalog(
                integration_id=integration_id,
                name=table_name,
                columns=inspector.get_columns(table_name=table_name, schema=schema_name),
                primary_keys=inspector.get_pk_constraint(table_name=table_name, schema=schema_name),
                foreign_keys=inspector.get_foreign_keys(table_name=table_name, schema=schema_name),
                indexes=inspector.get_indexes(table_name=table_name, schema=schema_name),
                table_comment=inspector.get_table_comment(table_name=table_name, schema=schema_name)
            )
            tables.append(table)
        except Exception as e:
            logger.error(f'Failed to inspect table {schema_name}.{table_name}: {e}', exc_info=True)
    
    return tuple(tables)


def _inspect_schemas(inspector: Inspector, integration_id: UUID, schema_spec: Specification, table_spec: Specification) -> Tuple[SchemaCatalog]:
    schema_names = inspector.get_schema_names()
    schemas = []

    for schema_name in schema_names:
        schema_candidate = SchemaCatalog(integration_id=integration_id, name=schema_name)
        if not schema_spec.is_satisfied_by(schema_candidate):
            continue
        tables = _inspect_tables(inspector, integration_id, schema_name, table_spec)
        if tables:
            schemas.append(SchemaCatalog(integration_id=integration_id, name=schema_name, tables=tables))

    return tuple(schemas)


def inspect_integration_registry(
    integration_ids: List[UUID],
    integration_spec: Specification,
    schema_spec: Specification,
    table_spec: Specification,
) -> IntegrationRegistryCatalog:
    integrations = []

    for integration_id in integration_ids:
        integration_meta_candidate = IntegrationCatalog(id=integration_id)
        if not integration_spec.is_satisfied_by(integration_meta_candidate):
            continue
        
        inspector = get_inspector(integration_id)
        if inspector is None:
            continue
        
        schemas = _inspect_schemas(inspector, integration_id, schema_spec, table_spec)
        if schemas:
            integrations.append(IntegrationCatalog(id=integration_id, schemas=schemas))

    return IntegrationRegistryCatalog(integrations=tuple(integrations))