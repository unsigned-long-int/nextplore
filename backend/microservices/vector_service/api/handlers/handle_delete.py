import uuid
import asyncio
from typing import List

from messaging.events.integration_service import IntegrationDeleted
from database.repositories import VectorRepository
from services.qdrant.delete import delete_qdrant_vectors
from services.pg.delete import delete_pg_vector_metadata
from shared.cache.service_caches.vector_cache import vector_service_cache


async def handle_vector_delete(event: IntegrationDeleted) -> None:
    print(f'vectorized meta will be deleted: {event}')
    vector_repo = VectorRepository()
    qdrant_vector_ids = await vector_repo.get_qdrant_vector_ids(event.integration_id)
    vector_ids = [str(id) for id in qdrant_vector_ids]
    
    await asyncio.gather(
        delete_pg_vector_metadata(event.integration_id),
        delete_qdrant_vectors(
            qdrant_vector_ids=vector_ids, 
            user_id=str(event.user_id),
            organization_id=str(event.organization_id)
        )
    )

    await vector_service_cache.delete_by_prefix(
        event.organization_id,
        event.user_id
    )