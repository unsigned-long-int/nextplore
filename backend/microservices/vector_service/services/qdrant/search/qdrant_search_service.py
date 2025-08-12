import os 
from typing import List
from uuid import UUID
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from nextplore_sdk.identity_service.identity_model.user_identity import UserIdentity


async def search_nearest_vectors(user_identity: UserIdentity, embedding: List[float], top_k: int = 5) -> List[UUID]:
    qdrant = AsyncQdrantClient(
        url=os.getenv('QDRANT_CLUSTER_HOST'), 
        api_key=os.getenv('QDRANT_API_KEY')
    )
    qd_filter = Filter(
        must=[
                FieldCondition(key='user_id', match=MatchValue(value=str(user_identity.user_id))),
                FieldCondition(key='organization_id', match=MatchValue(value=str(user_identity.organization_id)))
            ]
        )
    hits = await qdrant.search(
        collection_name='nextplore',
        query_vector=embedding,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
        query_filter=qd_filter
    )
    if not hits:
        return []
    
    return [UUID(hit.payload.get('qdrant_vector_id')) for hit in hits]
