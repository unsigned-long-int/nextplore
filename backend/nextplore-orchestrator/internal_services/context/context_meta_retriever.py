import pandas as pd
from uuid import UUID
from typing import List, Dict, Tuple, Optional

from internal_services.cosine_similarity import cosine_similarity


def retrieve_context_meta(
        query_vector: List[float],
        embedded_tables_df: pd.DataFrame,
        context_size: Optional[int] = 5
) -> Tuple[List[UUID], Dict[UUID, List[str]], Dict[UUID, List[str]]]:
    context_cosine_matrix = [
        (
            row['integration_id'],
            row['schema_name'],
            row['table_name'],
            cosine_similarity(
                query_embedding=query_vector,
                knowledge_embedding=row['embeddings']
            )
        )
        for _, row in embedded_tables_df.iterrows()
    ]
    
    context_cosine_matrix.sort(key=lambda similarity: similarity[3], reverse=True)
    context_cosine_matrix = context_cosine_matrix[:context_size - 1]

    integrations: List[UUID] = list({row[0] for row in context_cosine_matrix})

    schemas: Dict[UUID, List[str]] = {}
    tables: Dict[UUID, List[str]] = {}

    for row in context_cosine_matrix:
        integration_id = row[0]
        schema_name = row[1]
        table_name = row[2]

        schemas.setdefault(integration_id, []).append(schema_name)
        tables.setdefault(integration_id, []).append(table_name)

    return integrations, schemas, tables
