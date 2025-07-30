import uuid
import asyncio
from typing import List

from messaging.events.embedding_service import CrawlMetaEmbedded
from database.models import VectorORM
from services.qdrant.upsert import upsert_qdrant_vectors
from services.pg.upsert import upsert_pg_vector_metadata
from services.qdrant.models import QdrantVectorPoint


async def handle_vector_upsert(event: CrawlMetaEmbedded) -> None:
    print(f'vectorized meta will be upserted: {event}')
    pg_vectors: List[VectorORM] = []
    qdrant_vectors: List[QdrantVectorPoint] = []
    for embedding in event.orm_embedding:
        qdrant_vector_id = uuid.uuid4()
        pg_vectors.append(
            VectorORM(
                qdrant_vector_id=qdrant_vector_id,
                integration_id=embedding.integration_id,
                schema_name=embedding.schema_name,
                table_name=embedding.table_name,
                table_meta=embedding.table_meta.model_dump_json()
            )
        )
        qdrant_vectors.append(
            QdrantVectorPoint(
                id=qdrant_vector_id,
                user_id=event.user_id,
                organization_id=event.organization_id,
                vector=embedding.embedding
            )
        )

    await asyncio.gather(
        upsert_pg_vector_metadata(pg_vectors),
        upsert_qdrant_vectors(qdrant_vectors)
    )