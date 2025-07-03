import pandas as pd
from dataclasses import dataclass
from typing import List
from sqlalchemy import Engine
from openai import OpenAI

from core.vector_generation_service import VectorGenerator
from core.database.vectors_ingestion import IngestionServiceProtocol
from core.database.catalogs import IntegrationRegistryCatalog
from services.database.models import VectorORM, IntegrationORM
from services.database.dependencies import backend_session_scope


@dataclass
class UpsertService:
    client: OpenAI
    integration_registry: IntegrationRegistryCatalog
    ingestion_service: IngestionServiceProtocol

    def upsert_storage(self) -> None:
        orm_vectors = self._generate_vectors()
        self.ingestion_service.ingest_vectors(orm_vectors)

    def _generate_vectors(self) -> pd.DataFrame:
        orm_vectors = []
        for table_meta in self.integration_registry.table_metas:
            embedding_generator = VectorGenerator(
                client=self.client,
                datastream=repr(table_meta)
            )

            vector = embedding_generator.generate_vector()

            orm_vectors.append({
                'integration_id': table_meta['integration_id'],
                'schema_name': table_meta['schema_name'],
                'table_name': table_meta['table_name'],
                'table_meta': repr(table_meta),
                'vector': vector
            })

        return pd.DataFrame(orm_vectors)
