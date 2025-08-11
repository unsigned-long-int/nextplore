import logging
from typing import Tuple
from uuid import UUID
from sqlalchemy import quoted_name
from sqlalchemy.engine.reflection import Inspector

from utils.catalogs import (
    SchemaCatalog,
    TableCatalog
)
from utils.filters.logic import Specification


logger = logging.getLogger(__name__)


def crawl_tables(crawler: Inspector, integration_id: UUID, schema_name: str, table_spec: Specification) -> Tuple[TableCatalog]:
    table_names = crawler.get_table_names(schema=quoted_name(schema_name, quote=True))
    tables = []

    for table_name in table_names:
        table_candidate = TableCatalog(integration_id=integration_id, name=table_name)
        if not table_spec.is_satisfied_by(table_candidate):
            continue
        try:
            table = TableCatalog(
                integration_id=integration_id,
                name=table_name,
                columns=crawler.get_columns(table_name=table_name, schema=schema_name),
                primary_keys=crawler.get_pk_constraint(table_name=table_name, schema=schema_name),
                foreign_keys=crawler.get_foreign_keys(table_name=table_name, schema=schema_name),
                indexes=crawler.get_indexes(table_name=table_name, schema=schema_name),
                table_comment=crawler.get_table_comment(table_name=table_name, schema=schema_name)
            )
            tables.append(table)
        except Exception as e:
            logger.error(f'Failed to inspect table {schema_name}.{table_name}: {e}', exc_info=True)
    
    return tuple(tables)


def crawl_schemas(crawler: Inspector, integration_id: UUID, schema_spec: Specification, table_spec: Specification) -> Tuple[SchemaCatalog]:
    schema_names = crawler.get_schema_names()
    schemas = []

    for schema_name in schema_names:
        schema_candidate = SchemaCatalog(integration_id=integration_id, name=schema_name)
        print(f'schema is satisfed{schema_spec.is_satisfied_by(schema_candidate)}')
        if not schema_spec.is_satisfied_by(schema_candidate):
            continue
        tables = crawl_tables(crawler, integration_id, schema_name, table_spec)
        if tables:
            schemas.append(SchemaCatalog(integration_id=integration_id, name=schema_name, tables=tables))

    return tuple(schemas)
