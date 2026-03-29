import asyncio
import logging

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from kafka_messaging.events.integration_service import DataStoreDeleted
from vector_service.services.vector_store_service.store.store_service import VectorStoreService
from vector_service.services.vector_store_service.exceptions import DeleteVectorDBFailed
from vector_service.database.repositories import VectorRepository
from vector_service.database.exceptions import VectorDeleteFailed
from vector_service.cache import CacheService


logger = logging.getLogger(__name__)


async def handle_vector_delete(
    event: DataStoreDeleted,
    backend_connector: DatabaseBackendConnector,
    cache_service: CacheService,
    vector_store_service: VectorStoreService
) -> None:
    vector_repo = VectorRepository(backend_connector)
    qdrant_vector_ids = await vector_repo.get_qdrant_vector_ids(
        organization_id=event.organization_id,
        user_id=event.user_id,
        datastore_id=event.datastore_id
    )
    vector_ids = [str(v_id) for v_id in qdrant_vector_ids]
    
    try:
        await asyncio.gather(
            vector_repo.delete_vector_meta(
                organization_id=event.organization_id, 
                user_id=event.user_id,
                datastore_id=event.datastore_id
            ),
            vector_store_service.delete_vectors(
                vector_ids=vector_ids,
                user_id=str(event.user_id),
                organization_id=str(event.organization_id)
            )
        )

        await cache_service.cache.delete_by_prefix(
            event.organization_id,
            event.user_id
        )
    except VectorDeleteFailed as e:
        logger.error(
            f'Delete vector metadata failed with DB error: {str(e)}',
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    except DeleteVectorDBFailed as e:
        logger.error(
            f'Delete vector from vector DB failed with client error: {str(e)}',
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    except Exception as e:
        logger.error(
            f'Unexpected error by handling delete vectors: {str(e)}',
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
