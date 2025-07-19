import json
import pandas as pd

from messaging.events.embedding_service import CrawlMetaEmbedded
from services import upsert


def handle_vector_upsert(event: CrawlMetaEmbedded) -> None:
    print(f'vectorized meta will be upserted: {event}')
    orm_embedding = pd.DataFrame([{
        **embedding.model_dump(exclude={'table_meta'}),
        'table_meta': embedding.table_meta.model_dump_json()
    } for embedding in event.orm_embedding])

    orm_embedding.rename(columns={'embedding': 'vector'}, inplace=True)
    upsert(orm_embedding)
