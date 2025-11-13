import json 
from typing import List, Dict
from collections import defaultdict

from nextplore_orchestrator.clients.vector.models.vector_meta_response import VectorMetaResponse
from .rag_context import RAGContext


def dictify(d):
    if isinstance(d, defaultdict):
        return {k: dictify(v) for k, v in d.items()}
    return d


def build_rag_context(
    vectors_meta: List[VectorMetaResponse]
) -> RAGContext:
    integrations = {str(meta.integration_id) for meta in vectors_meta}
    schemas = {str(meta.schema_name) for meta in vectors_meta}
    tables = {str(meta.table_name) for meta in vectors_meta}
    columns = {
        str(col) for meta in vectors_meta
        for col in meta.table_meta.column_names
    }

    registry: Dict[str, Dict[str, Dict[str, List[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for meta in vectors_meta:
        integration_id = str(meta.integration_id)
        schema_name = str(meta.schema_name)
        table_name = str(meta.table_name)
        column_names = meta.table_meta.column_names
        column_names = [str(col) for col in column_names]

        registry[integration_id][schema_name][table_name] = column_names

    clean_registry = dictify(registry)
    return RAGContext(
        integration_registry_repr=json.dumps(clean_registry, indent=2),
        integrations_enum=list(integrations),
        schemas_enum=list(schemas),
        tables_enum=list(tables),
        columns_enum=list(columns)
    )
