from uuid import UUID
from typing import List, Dict, Tuple

from shared.contracts.vector_service import VectorMetaResponse


def retrieve_context_meta(
    vectors_meta: List[VectorMetaResponse]
) -> Tuple[List[UUID], Dict[UUID, List[str]], Dict[UUID, List[str]]]:
    integrations: List[UUID] = list(vector_meta.integration_id for vector_meta in vectors_meta)

    schemas: Dict[UUID, List[str]] = {}
    tables: Dict[UUID, List[str]] = {}

    for vector_meta in vectors_meta:
        integration_id = vector_meta.integration_id
        schema_name = vector_meta.schema_name
        table_name = vector_meta.table_name

        schemas.setdefault(integration_id, []).append(schema_name)
        tables.setdefault(integration_id, []).append(table_name)

    return integrations, schemas, tables
