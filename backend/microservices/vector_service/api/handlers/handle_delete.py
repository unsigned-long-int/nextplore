import asyncio
import logging

from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from messaging.events.integration_service import IntegrationDeleted
from services.vector_store_service.store import VectorStoreService
from services.vector_store_service.exceptions import DeleteVectorDBFailed
from database.repositories import VectorRepository
from database.exceptions import VectorDeleteFailed
from cache import CacheService


logger = logging.getLogger(__name__)

async def handle_vector_delete(
    event: IntegrationDeleted, 
    connector: DatabaseBackendConnector, 
    cache_service: CacheService,
    vector_store_service: VectorStoreService
) -> None:
    vector_repo = VectorRepository(connector)
    qdrant_vector_ids = await vector_repo.get_qdrant_vector_ids(
        organization_id=event.organization_id,
        user_id=event.user_id,
        integration_id=event.integration_id
    )
    vector_ids = [str(id) for id in qdrant_vector_ids]
    
    try:
        await asyncio.gather(
            vector_repo.delete_vector_meta(
                organization_id=event.organization_id, 
                user_id=event.user_id,
                integration_id=event.integration_id
            ),
            vector_store_service.delete_vectors(
                vector_ids=vector_ids,
                user_id=str(event.user_id),
                organization_id=str(event.organization_id)
            ),
            return_exceptions=True
        )

        await cache_service.cache.delete_by_prefix(
            event.organization_id,
            event.user_id
        )
    except VectorDeleteFailed as e:
        logger.error(
            f'Delete vector metadata failed with DB error: {e}', 
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    except DeleteVectorDBFailed as e:
        logger.error(
            f'Delete vector from vector DB failed with client error: {e}', 
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    except Exception as e:
        logger.error(
            f'Unexpected error by handling delete vectors: {e}', 
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
