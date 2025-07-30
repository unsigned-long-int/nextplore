import os 
from typing import List
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from services.qdrant.models import QdrantVectorPoint


async def upsert_qdrant_vectors(qdrant_vector_points: List[QdrantVectorPoint]) -> None:
    qdrant = AsyncQdrantClient(
        url=os.getenv('QDRANT_CLUSTER_HOST'), 
        api_key=os.getenv('QDRANT_API_KEY')
    )
    points = [
        PointStruct(
            id=str(point.id),
            vector=point.vector,
            payload={
                'qdrant_vector_id': str(point.id),
                'user_id': str(point.user_id),
                'organization_id': str(point.organization_id)
            }
        )
        for point in qdrant_vector_points
    ]
    await qdrant.upsert(
        collection_name='nextplore',
        points=points
    )