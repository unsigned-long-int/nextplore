import pandas as pd

from queue import Queue
from openai import OpenAI
from dataclasses import dataclass

from infrastructure.vector_generation_service import VectorGenerator
from infrastructure.storage.ingestion_service import IngestionServiceProtocol
from infrastructure.storage.database_inspection_service import DatabaseDescriptor


@dataclass
class UpsertOrchestrationService:
    client: OpenAI
    database_descriptor: DatabaseDescriptor
    ingestion_service: IngestionServiceProtocol

    def upsert_storage(self, progress_queue: Queue) -> None:
        progress_queue.put('generating meta vectors...')
        orm_vectors = self.generate_vectors()
        progress_queue.put(
            f'upserting vectors to: {self.ingestion_service}...')
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
                'schema_name': table_meta['schema_name'],
                'table_name': table_meta['table_name'],
                'table_meta': repr(table_meta),
                'embedding': vector
            })
        return pd.DataFrame(orm_vectors)
