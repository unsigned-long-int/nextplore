from typing import List
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.engine import Row

from database.models import VectorORM
from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector


class VectorRepository:
    def __init__(self) -> None:
        self.database_backend_connector = DatabaseBackendConnector()

    async def get_vector_profiles(self, integration_id: UUID) -> List[Row]:
        if not integration_id:
            return []
        
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(
                    VectorORM.integration_id,
                    VectorORM.schema_name,
                    VectorORM.table_name,
                    VectorORM.table_meta
                )
                .where(VectorORM.integration_id == integration_id)
            )
            vectors = result.all()
            return vectors

    async def get_vectors(self, vector_ids: List[UUID]) -> List[Row]:
        print(f'requested vectors: {vector_ids}')
        if not vector_ids:
            return []
        
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(
                    VectorORM.integration_id,
                    VectorORM.schema_name,
                    VectorORM.table_name,
                    VectorORM.table_meta,
                    )
                .where(VectorORM.qdrant_vector_id.in_(vector_ids))
            )
            vectors = result.all()
            return vectors
        
    async def get_vector_count(self, integration_ids: List[UUID]) -> int:
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(func.count())
                .select_from(VectorORM)
                .where(VectorORM.integration_id.in_(integration_ids))
            )
            vectors_number = result.scalar_one()
            return vectors_number
        
    async def upsert_vector_meta(self, vectors_orm: List[VectorORM]) -> None:
        async with self.database_backend_connector.session_scope() as scoped_session:
            scoped_session.add_all(vectors_orm)
            await scoped_session.flush()
    
    async def delete_vector_meta(self, integration_id: UUID) -> None:
        async with self.database_backend_connector.session_scope() as scoped_session:
            stmt = (
                delete(VectorORM)
                .where(
                    VectorORM.integration_id == integration_id
                )
            )
            await scoped_session.execute(stmt)

    async def get_qdrant_vector_ids(self, integration_id: UUID) -> List[UUID]:
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(VectorORM.qdrant_vector_id)
                .where(VectorORM.integration_id == integration_id)
            )
            qdrant_vector_ids = result.scalars().all()
            return qdrant_vector_ids
        