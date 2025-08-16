import logging
from typing import List
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.engine import Row
from sqlalchemy.exc import SQLAlchemyError


from database.exceptions import (
    VectorGetFailed,
    VectorProfilesGetFailed,
    VectorCountGetFailed,
    VectorUpsertFailed,
    VectorDeleteFailed
)
from database.models.vector_orm import VectorORM
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)

class VectorRepository:
    def __init__(self, db_connector: DatabaseBackendConnector) -> None:
        self._db = db_connector

    async def get_vector_profiles(self, organization_id: UUID, user_id: UUID, integration_id: UUID) -> List[Row]:
        try:
            if not integration_id:
                logger.warning(f'No integration id provided. ', extra={'org_id': organization_id, 'user_id': user_id})
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
        except SQLAlchemyError as e:
            logger.error(f'Get vector profiles failed: {e}', exc_info=True)
            raise VectorProfilesGetFailed from e

    async def get_vectors(self, organization_id: UUID, user_id: UUID, vector_ids: List[UUID]) -> List[Row]:
        try:
            if not vector_ids:
                logger.warning(f'No vectors requested. ', extra={'org_id': organization_id, 'user_id': user_id})
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
        except SQLAlchemyError as e:
            logger.error(f'Get vectors failed: {e}', exc_info=True)
            raise VectorGetFailed from e

        
    async def get_vector_count(self, organization_id: UUID, user_id: UUID) -> int:
        try:
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
        except SQLAlchemyError as e:
            logger.error(f'Get vector count failed: {e}', exc_info=True)
            raise VectorCountGetFailed from e
        
    async def upsert_vector_meta(self, organization_id: UUID, user_id: UUID, vectors_orm: List[VectorORM]) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add_all(vectors_orm)
                await scoped_session.flush()
        except SQLAlchemyError as e:
            logger.error(f'Upsert vectors failed: {e}', exc_info=True)
            raise VectorUpsertFailed from e

    async def delete_vector_meta(self, organization_id: UUID, user_id: UUID, integration_id: UUID) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                stmt = (
                    delete(VectorORM)
                    .where(
                        VectorORM.integration_id == integration_id
                    )
                )
                await scoped_session.execute(stmt)
        except SQLAlchemyError as e:
            logger.error(f'Delete vectors failed: {e}', exc_info=True)
            raise VectorDeleteFailed from e

    async def get_qdrant_vector_ids(self, organization_id: UUID, user_id: UUID, integration_id: UUID) -> List[UUID]:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            result = await scoped_session.execute(
                select(VectorORM.qdrant_vector_id)
                .where(VectorORM.integration_id == integration_id)
            )
            qdrant_vector_ids = result.scalars().all()
            return qdrant_vector_ids
        