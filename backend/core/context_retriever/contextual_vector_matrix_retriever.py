import pandas as pd

from typing import List, Tuple, Optional

from core.cosine_similarity import cosine_similarity


def retrieve_contextual_vector_matrix(
        query_vector: List[float],
        orm_vectors: pd.DataFrame,
        context_size: Optional[int] = 5
) -> pd.DataFrame:
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
    context_cosine_matrix = context_cosine_matrix[:context_size-1]

    return pd.DataFrame(
        context_cosine_matrix,
        columns=[
            'integration_id',
            'schema_name',
            'table_name',
            'table_meta',
            'similarity_score'
        ]
    )
