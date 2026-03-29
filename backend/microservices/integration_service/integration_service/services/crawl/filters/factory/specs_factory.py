from typing import List, Dict, Tuple
from uuid import UUID

from integration_service.services.crawl.filters.specs import (
    DataStoreIdSpec,
    SchemaNameSpec,
    TableNameSpec
)


def create_specs(
        datastores: List[UUID],
        schemas: Dict[str, List[str]],
        tables: Dict[str, List[str]]
) -> Tuple[DataStoreIdSpec, SchemaNameSpec, TableNameSpec]:
    datastore_spec = DataStoreIdSpec(datastore_ids=set(datastores))
    schema_spec = SchemaNameSpec(allowed_datastore_schemas={UUID(key): set(values) for key, values in schemas.items()})
    table_spec = TableNameSpec(allowed_datastore_tables={UUID(key): set(values) for key, values in tables.items()})

    return datastore_spec, schema_spec, table_spec
