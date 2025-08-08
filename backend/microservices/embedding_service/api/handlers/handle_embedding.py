import asyncio
import logging
from typing import List

from services.embedding_service import embed
from nextplore_shared.contracts.embedding_service.query_embedding_request import QueryEmbeddingRequest
from nextplore_shared.contracts.embedding_service.embedding_response import EmbeddingResponse
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationMetaCrawled
from messaging.events.embedding_service import CrawlMetaEmbedded, ORMEmbedding, TableMeta


logger = logging.getLogger(__name__)

async def handle_query_embedding(embedding_request: QueryEmbeddingRequest) -> EmbeddingResponse:
    embedding = await embed(embedding_request.datastream)
    return EmbeddingResponse(embedding=embedding)

async def handle_crawl_meta_embedding(event: IntegrationMetaCrawled) -> None:
    embedding_tasks = [embed(repr(meta)) for meta in event.table_metas]
    embeddings = await asyncio.gather(*embedding_tasks)

    orm_embeddings: List[ORMEmbedding] = []
    for meta, vector in zip(event.table_metas, embeddings):
        orm_embeddings.append(ORMEmbedding(
            integration_id=meta.integration_id,
            schema_name=meta.schema_name,
            table_name=meta.table_name,
            table_meta=TableMeta(**meta.model_dump()),
            embedding=vector
        ))

    await get_kafka_message_bus().publish(CrawlMetaEmbedded(
        user_id=event.user_id,
        organization_id=event.organization_id,
        orm_embedding=orm_embeddings
    ))