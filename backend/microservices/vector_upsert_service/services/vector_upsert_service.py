import os
import pandas as pd
from dataclasses import dataclass

from shared.database.sql_connection_service import fetch_engine
from utils.vectors_ingestion import IngestionServiceProtocol, PgVectorIngestionService


@dataclass
class Upserter:
    orm_vectors: pd.DataFrame
    ingestion_service: IngestionServiceProtocol

    def upsert_vectors(self) -> None:
        self.ingestion_service.ingest_vectors(self.orm_vectors)


def upsert(orm_vectors: pd.DataFrame) -> None:
    DATABASE_URL = f'postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}'
    engine = fetch_engine(DATABASE_URL)
    pg_vector_ingestion_service = PgVectorIngestionService(engine)

    upserter = Upserter(
        orm_vectors=orm_vectors,
        ingestion_service=pg_vector_ingestion_service
    )
    upserter.upsert_vectors()