import uuid
import pandas as pd

from openai import OpenAI
from dataclasses import dataclass

from core.vector_generation_service import VectorGenerator
from core.database.database_metadata_ingestor import IngestionServiceProtocol
from core.database.user_database_inspector import DatabaseDescriptor


@dataclass
class UpsertOrchestrationService:
    client: OpenAI
    database_descriptor: DatabaseDescriptor
    ingestion_service: IngestionServiceProtocol

    def upsert_storage(self) -> None:
        orm_vectors = self.generate_vectors()
        self.ingestion_service.ingest_vectors(orm_vectors)

    def generate_vectors(self) -> pd.DataFrame:
        orm_vectors = []
        for table_meta in self.database_descriptor.table_metas:
            embedding_generator = VectorGenerator(
                client=self.client,
                datastream=repr(table_meta)
            )

            vector = embedding_generator.generate_vector()

            orm_vectors.append({
                'id': uuid.uuid4(),
                'schema_name': table_meta['schema_name'],
                'table_name': table_meta['table_name'],
                'table_meta': repr(table_meta),
                'vector': vector
            })
        return pd.DataFrame(orm_vectors)
