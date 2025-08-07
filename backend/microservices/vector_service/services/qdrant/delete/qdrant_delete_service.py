import os
from typing import List
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny, FilterSelector


async def delete_qdrant_vectors(
    qdrant_vector_ids: List[str],
    user_id: str,
    organization_id: str
) -> None:
    qdrant = AsyncQdrantClient(
        url=os.getenv('QDRANT_CLUSTER_HOST'),
        api_key=os.getenv('QDRANT_API_KEY')
    )

    conditions = [
        FieldCondition(
            key='qdrant_vector_id',
            match=MatchAny(any=qdrant_vector_ids)
        ),
        FieldCondition(
            key='organization_id',
            match=MatchValue(value=organization_id)
        ),
        FieldCondition(
            key='user_id',
            match=MatchValue(value=user_id)
        )
    ]

    qd_filter = Filter(must=conditions)

    await qdrant.delete(
        collection_name='nextplore',
        points_selector=FilterSelector(
            filter=qd_filter
        )
    )
