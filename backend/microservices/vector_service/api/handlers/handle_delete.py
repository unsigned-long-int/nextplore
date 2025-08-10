import asyncio

from messaging.events.integration_service import IntegrationDeleted
from database.repositories import VectorRepository
from services.qdrant.delete import delete_qdrant_vectors
from services.pg.delete import delete_pg_vector_metadata
from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_shared.cache.service_caches.vector_cache.cache import vector_service_cache


async def handle_vector_delete(event: IntegrationDeleted, connector: DatabaseBackendConnector) -> None:
    vector_repo = VectorRepository(connector)
    qdrant_vector_ids = await vector_repo.get_qdrant_vector_ids(
        organization_id=event.organization_id,
        user_id=event.user_id,
        integration_id=event.integration_id
    )
    vector_ids = [str(id) for id in qdrant_vector_ids]
    
    await asyncio.gather(
        delete_pg_vector_metadata(
            connector=connector,
            organization_id=event.organization_id,
            user_id=event.user_id,
            integration_id=event.integration_id
        ),
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