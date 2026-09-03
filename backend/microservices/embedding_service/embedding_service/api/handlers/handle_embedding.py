import asyncio
import logging

from kafka_messaging.events.embedding_service import (
    CrawlMetaEmbedded,
    ORMEmbedding,
    TableMeta,
)
from kafka_messaging.events.integration_service import DataStoreMetaCrawled
from kafka_messaging.message_bus import get_kafka_message_bus

from embedding_service.services.embedding.embedder_factory import dispatch_embedder

logger = logging.getLogger(__name__)


async def handle_crawl_meta_embedding(event: DataStoreMetaCrawled) -> None:
    embedder_cls = dispatch_embedder()
    embedder = embedder_cls()
    embedding_tasks = [
        embedder.generate_embedding(repr(meta)) for meta in event.table_metas
    ]
    embeddings = await asyncio.gather(*embedding_tasks)

    orm_embeddings: list[ORMEmbedding] = []
    for meta, vector in zip(event.table_metas, embeddings):
        orm_embeddings.append(
            ORMEmbedding(
                datastore_id=meta.datastore_id,
                schema_name=meta.schema_name,
                table_name=meta.table_name,
                table_meta=TableMeta(**meta.model_dump()),
                embedding=vector,
            )
        )

    await get_kafka_message_bus().publish(
        CrawlMetaEmbedded(
            user_id=event.user_id,
            organization_id=event.organization_id,
            orm_embedding=orm_embeddings,
        )
    )
