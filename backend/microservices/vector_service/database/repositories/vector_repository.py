from typing import List
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.engine import Row

from nextplore_shared.database.models.vector_orm import VectorORM
from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector


class VectorRepository:
    def __init__(self, db_connector: DatabaseBackendConnector) -> None:
        self._db = db_connector

    async def get_vector_profiles(self, organization_id: UUID, user_id: UUID, integration_id: UUID) -> List[Row]:
        if not integration_id:
            return []
        
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
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

    async def get_vectors(self, organization_id: UUID, user_id: UUID, vector_ids: List[UUID]) -> List[Row]:
        if not vector_ids:
            return []
        
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
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
        
    async def get_vector_count(self, organization_id: UUID, user_id: UUID) -> int:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            result = await scoped_session.execute(
                select(func.count())
                .select_from(VectorORM)
                .where(
                    VectorORM.organization_id == organization_id, 
                    VectorORM.user_id == user_id
                )
            )
            vectors_number = result.scalar_one()
            return vectors_number
        
    async def upsert_vector_meta(self, organization_id: UUID, user_id: UUID, vectors_orm: List[VectorORM]) -> None:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            scoped_session.add_all(vectors_orm)
            await scoped_session.flush()
    
    async def delete_vector_meta(self, organization_id: UUID, user_id: UUID, integration_id: UUID) -> None:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            stmt = (
                delete(VectorORM)
                .where(
                    VectorORM.integration_id == integration_id
                )
            )
            await scoped_session.execute(stmt)

    async def get_qdrant_vector_ids(self, organization_id: UUID, user_id: UUID, integration_id: UUID) -> List[UUID]:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            result = await scoped_session.execute(
                select(VectorORM.qdrant_vector_id)
                .where(VectorORM.integration_id == integration_id)
            )
            qdrant_vector_ids = result.scalars().all()
            return qdrant_vector_ids
        