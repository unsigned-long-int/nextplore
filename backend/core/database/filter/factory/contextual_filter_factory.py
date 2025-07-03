import pandas as pd
from typing import Tuple, Dict
from uuid import UUID
from typing import Set

from core.database.filter.specs import IntegrationIdSpec, SchemaNameSpec, TableNameSpec
from core.database.filter.logic import Specification


def create_contextual_filters(contextual_vector_matrix: pd.DataFrame) -> Tuple[Specification, Specification, Specification]:
    integration_ids: Set[UUID] = set(contextual_vector_matrix['integration_id'])
    integration_spec = IntegrationIdSpec(set(integration_ids))

    schema_map: Dict[UUID, Set[str]] = (
        contextual_vector_matrix
        .groupby('integration_id')['schema_name']
        .agg(set)
        .to_dict()
    )
    schema_spec = SchemaNameSpec(schema_map)

    table_map: Dict[UUID, Dict[str, Set[str]]] = {}
    for _, row in contextual_vector_matrix.iterrows():
        iid = row['integration_id']
        table = row['table_name']
        table_map.setdefault(iid, set()).add(table)

    table_spec = TableNameSpec(table_map)

    return integration_spec, schema_spec, table_spec
