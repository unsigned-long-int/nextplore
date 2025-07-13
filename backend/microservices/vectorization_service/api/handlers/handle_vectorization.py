from typing import List, Dict

from shared.contracts.vectorization_service import QueryVectorRequest, VectorResponse
from services import vectorize
from messaging.message_bus import get_kafka_message_bus
from messaging.events import events


def handle_query_vectorization(vector_request: QueryVectorRequest) -> VectorResponse:
    datastream = vector_request.datastream
    vector = vectorize(datastream)

    return VectorResponse(vector=vector)


def handle_crawl_meta_vectorization(event: events.IntegrationMetaCrawled) -> None:
    print(f'crawled meta will be vectorized: {event}')
    orm_vectors: List[Dict[str, str]] = []
    for table_meta in event.table_metas:
        vector = vectorize(datastream=table_meta['repr'])

        orm_vectors.append({
            'integration_id': table_meta['integration_id'],
            'schema_name': table_meta['schema_name'],
            'table_name': table_meta['table_name'],
            'table_meta': table_meta['repr'],
            'vector': vector
        })

    print(f'meta vectorized: {orm_vectors}')
    get_kafka_message_bus().publish(events.CrawlMetaVectorized(orm_vectors=orm_vectors))
