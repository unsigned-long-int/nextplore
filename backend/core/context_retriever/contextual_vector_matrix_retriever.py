import pandas as pd

from typing import List, Tuple, Optional

from infrastructure.cosine_similarity import cosine_similarity


def retrieve_contextual_vector_matrix(
        query_vector: List[float],
        orm_vectors: pd.DataFrame,
        context_size: Optional[int] = 5
) -> List[Tuple[str, str, str, float]]:
    context_cosine_matrix = [
        (
            row['schema_name'],
            row['table_name'],
            row['table_meta'],
            cosine_similarity(
                query_embedding=query_vector,
                knowledge_embedding=row['embedding']
            )
        )
        for i, row in orm_vectors.iterrows()
    ]
    context_cosine_matrix.sort(
        key=lambda similarity: similarity[3],
        reverse=True
    )
    context_cosine_matrix = context_cosine_matrix[:context_size-1]
    return context_cosine_matrix
