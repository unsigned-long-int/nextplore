import json
from collections import defaultdict

from nextplore_orchestrator.domain.models import RagContext, VectorNeighbour


def dictify(d):
    if isinstance(d, defaultdict):
        return {k: dictify(v) for k, v in d.items()}
    return d


def build_rag_context(vector_neighbours: list[VectorNeighbour]) -> RagContext:
    datastores = {str(vn.orm_metadata.datastore_id) for vn in vector_neighbours}
    schemas = {str(vn.orm_metadata.schema_name) for vn in vector_neighbours}
    tables = {str(vn.orm_metadata.table_name) for vn in vector_neighbours}
    columns = {
        str(col) for vn in vector_neighbours for col in vn.orm_metadata.column_names
    }

    registry: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for vn in vector_neighbours:
        datastore_id = str(vn.orm_metadata.datastore_id)
        schema_name = str(vn.orm_metadata.schema_name)
        table_name = str(vn.orm_metadata.table_name)
        column_names = vn.orm_metadata.column_names
        column_names = [str(col) for col in column_names]

        registry[datastore_id][schema_name][table_name] = column_names

    clean_registry = dictify(registry)
    return RagContext(
        datastore_registry_repr=json.dumps(clean_registry, indent=2),
        datastores_enum=list(datastores),
        schemas_enum=list(schemas),
        tables_enum=list(tables),
        columns_enum=list(columns),
        table_columns_registry=clean_registry,
    )
