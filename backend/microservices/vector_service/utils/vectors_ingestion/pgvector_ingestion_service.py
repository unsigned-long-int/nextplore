import pandas as pd
from sqlalchemy import Engine, types
from dataclasses import dataclass


@dataclass
class PgVectorIngestionService:
    engine: Engine

    def ingest_vectors(self, embedding: pd.DataFrame) -> None:
        embedding.to_sql(
            'vectors', 
            con=self.engine,
            schema='embeddings', 
            if_exists='append', 
            index=False,
            dtype={'table_meta': types.JSON}
        )
