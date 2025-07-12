import pandas as pd

from typing import List, Dict, Tuple, Optional

from internal_services.cosine_similarity import cosine_similarity


def retrieve_context_meta(
        query_vector: List[float],
        orm_vectors: pd.DataFrame,
        context_size: Optional[int] = 5
) -> Tuple[List[str], Dict[str, List[str]], Dict[str, List[str]]]:
    context_cosine_matrix = [
        (
            row['integration_id'],
            row['schema_name'],
            row['table_name'],
            row['table_meta'],
            cosine_similarity(
                query_embedding=query_vector,
                knowledge_embedding=row['vector']
            )
        )
        for _, row in orm_vectors.iterrows()
    ]
    context_cosine_matrix.sort(
        key=lambda similarity: similarity[4],
        reverse=True
    )
    
    context_cosine_matrix.sort(key=lambda similarity: similarity[4], reverse=True)
    context_cosine_matrix = context_cosine_matrix[:context_size - 1]

    integrations: List[str] = list({row[0] for row in context_cosine_matrix})

    schemas: Dict[str, List[str]] = {}
    tables: Dict[str, List[str]] = {}

    for row in context_cosine_matrix:
        integration_id = row[0]
        schema_name = row[1]
        table_name = row[2]

        schemas.setdefault(integration_id, []).append(schema_name)
        tables.setdefault(integration_id, []).append(table_name)

    return integrations, schemas, tables
