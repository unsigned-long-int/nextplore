import logging
from typing import List
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.engine import Row
from sqlalchemy.exc import SQLAlchemyError


from vector_service.database.exceptions import (
    VectorGetFailed,
    VectorProfilesGetFailed,
    VectorCountGetFailed,
    VectorUpsertFailed,
    VectorDeleteFailed
)
from vector_service.database.models import VectorORM
from vector_service.domain.models import VectorProfile
from vector_service.domain.mappers import orm_to_domain_vector_profile
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)


class VectorRepository:
    def __init__(self, backend_connector: DatabaseBackendConnector) -> None:
        self._db = backend_connector

    async def get_profiles(self, organization_id: UUID, user_id: UUID, datastore_id: UUID) -> List[VectorProfile]:
        try:
            if not datastore_id:
                logger.warning('No data store id provided.', extra={'org_id': organization_id, 'user_id': user_id})
                return []
            
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(VectorORM)
                    .where(VectorORM.datastore_id == datastore_id)
                )
                vectors = result.scalars().all()
                return [orm_to_domain_vector_profile(vector) for vector in vectors]
        except SQLAlchemyError as e:
            msg = f'Get vector profiles failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise VectorProfilesGetFailed(msg) from e

    async def get_vectors(self, organization_id: UUID, user_id: UUID, vector_ids: List[UUID]) -> List[Row]:
        try:
            if not vector_ids:
                logger.warning('No vectors requested. ', extra={'org_id': organization_id, 'user_id': user_id})
                return []
            
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(
                        VectorORM.qdrant_vector_id,
                        VectorORM.datastore_id,
                        VectorORM.schema_name,
                        VectorORM.table_name,
                        VectorORM.table_meta,
                        )
                    .where(VectorORM.qdrant_vector_id.in_(vector_ids))
                )
                vectors = result.all()
                return vectors
        except SQLAlchemyError as e:
            msg = f'Get vectors failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise VectorGetFailed(msg) from e

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
            msg = f'Get vector count failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise VectorCountGetFailed(msg) from e
        
    async def upsert_vector_meta(self, organization_id: UUID, user_id: UUID, vectors_orm: List[VectorORM]) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add_all(vectors_orm)
                await scoped_session.flush()
        except SQLAlchemyError as e:
            msg = f'Upsert vectors failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise VectorUpsertFailed(msg) from e

    async def delete_vector_meta(self, organization_id: UUID, user_id: UUID, datastore_id: UUID) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                stmt = (
                    delete(VectorORM)
                    .where(
                        VectorORM.datastore_id == datastore_id
                    )
                )
                await scoped_session.execute(stmt)
        except SQLAlchemyError as e:
            msg = f'Delete vectors failed with database error: {e}'
            logger.error(msg, exc_info=True)
            raise VectorDeleteFailed(msg) from e

    async def get_qdrant_vector_ids(self, organization_id: UUID, user_id: UUID, datastore_id: UUID) -> List[UUID]:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            result = await scoped_session.execute(
                select(VectorORM.qdrant_vector_id)
                .where(VectorORM.datastore_id == datastore_id)
            )
            qdrant_vector_ids = result.scalars().all()
            return qdrant_vector_ids
        