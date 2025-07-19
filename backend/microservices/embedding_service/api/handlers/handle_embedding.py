from typing import List, Dict

from services import embed
from shared.contracts.embedding_service import QueryEmbeddingRequest, EmbeddingResponse
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationMetaCrawled
from messaging.events.embedding_service import CrawlMetaEmbedded, ORMEmbedding, TableMeta


def handle_query_embedding(embedding_request: QueryEmbeddingRequest) -> EmbeddingResponse:
    datastream = embedding_request.datastream
    embedding = embed(datastream)

    return EmbeddingResponse(embedding=embedding)


def handle_crawl_meta_embedding(event: IntegrationMetaCrawled) -> None:
    print(f'crawled meta will be vectorized: {event}')
    orm_embedding: List[ORMEmbedding] = []
    for table_meta in event.table_metas:
        print(f'repr: {repr(table_meta)}')
        embedding = embed(datastream=repr(table_meta))

        orm_embedding.append(
            ORMEmbedding(
                integration_id=table_meta.integration_id,
                schema_name=table_meta.schema_name,
                table_name=table_meta.table_name,
                table_meta=TableMeta(**table_meta.model_dump()),
                embedding=embedding
            )
        )
    print(f'meta vectorized: {orm_embedding}')
    get_kafka_message_bus().publish(CrawlMetaEmbedded(orm_embedding=orm_embedding))
