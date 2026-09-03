from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.inspection import inspect

from integration_service.services.crawl.catalog_builder.inspectors import (
    inspect_schemas,
)
from integration_service.services.crawl.filters.logic import Specification


def build_schemas_catalog(
    engine: Engine,
    datastore_id: UUID,
    schema_spec: Specification,
    table_spec: Specification,
):
    with engine.connect() as conn:
        crawler = inspect(conn)
        schemas = inspect_schemas(
            crawler=crawler,
            datastore_id=datastore_id,
            schema_spec=schema_spec,
            table_spec=table_spec,
        )
        return schemas
