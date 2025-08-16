import uuid
import logging
import asyncio
from typing import List

from messaging.events.embedding_service import CrawlMetaEmbedded
from services.vector_store_service.store import VectorStoreService
from services.vector_store_service.models import VectorPoint
from services.vector_store_service.exceptions import UpsertVectorDBFailed
from database.models.vector_orm import VectorORM
from database.repositories import VectorRepository
from database.exceptions import VectorUpsertFailed
from cache import CacheService
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)

async def handle_vector_upsert(
    event: CrawlMetaEmbedded, 
    connector: DatabaseBackendConnector,
    cache_service: CacheService,
    vector_store_service: VectorStoreService
) -> None:
    pg_vectors: List[VectorORM] = []
    qdrant_vectors: List[VectorPoint] = []
    for embedding in event.orm_embedding:
        qdrant_vector_id = uuid.uuid4()
        pg_vectors.append(
            VectorORM(
                user_id=event.user_id,
                organization_id=event.organization_id,
                qdrant_vector_id=qdrant_vector_id,
                integration_id=embedding.integration_id,
                schema_name=embedding.schema_name,
                table_name=embedding.table_name,
                table_meta=embedding.table_meta.model_dump_json()
            )
        )
        qdrant_vectors.append(
            VectorPoint(
                id=qdrant_vector_id,
                user_id=event.user_id,
                organization_id=event.organization_id,
                vector=embedding.embedding
            )
        )

    vector_repo = VectorRepository(connector)
    try:
        await asyncio.gather(
            vector_repo.upsert_vector_meta(
                organization_id=event.organization_id, 
                user_id=event.user_id, 
                vectors_orm=pg_vectors
            ),
            vector_store_service.upsert_vectors(vector_points=qdrant_vectors),
            return_exceptions=True
        )

        await cache_service.cache.delete_by_prefix(
            event.organization_id,
            event.user_id
        )
    except VectorUpsertFailed as e:
        logger.error(
            f'Upsert vector metadata failed with DB error: {e}', 
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    except UpsertVectorDBFailed as e:
        logger.error(
            f'Upsert vector to vector DB failed with client error: {e}', 
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    except Exception as e:
        logger.error(
            f'Unexpected error by handling upsert vectors: {e}', 
            exc_info=True,
            extra={'org_id': event.organization_id, 'user_id': event.user_id}
        )
        raise
    