import pandas as pd

from messaging.events import events
from services import upsert


def handle_vector_upsert(event: events.CrawlMetaVectorized) -> None:
    print(f'vectorized meta will be upserted: {event}')
    orm_vectors = pd.DataFrame(event.orm_vectors)
    upsert(orm_vectors)
