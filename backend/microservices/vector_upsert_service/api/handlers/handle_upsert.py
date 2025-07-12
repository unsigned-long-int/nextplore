import pandas as pd

from messaging.events import events
from messaging.message_bus import get_kafka_message_bus
from services import upsert


def handle_vector_upsert(event: events.CrawlMetaVectorized) -> None:
    orm_vectors = pd.DataFrame(event.orm_vectors)
    upsert(orm_vectors)


get_kafka_message_bus().subscribe(event_cls=events.CrawlMetaVectorized, handler=handle_vector_upsert)
