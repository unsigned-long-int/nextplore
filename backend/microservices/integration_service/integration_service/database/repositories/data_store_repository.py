import logging
from typing import List, Dict
from uuid import UUID
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from svc_integration_contracts.models import CertState

from integration_service.domain.models.datastore import (
    DataStoreUpdate,
    DataStoreCreate,
    DataStoreProfile,
    DataStore
)
from integration_service.domain.models.secret import DataStoreSecret, SecretType
from integration_service.domain.models.cert import CertProfile
from integration_service.domain.mappers.datastore import (
    orm_from_datastore_create,
    datastore_profile_from_orm,
    datastore_from_orm
)
from integration_service.domain.mappers.secret import orm_from_secrets, secrets_from_orm
from integration_service.domain.mappers.cert import orm_from_cert, cert_profile_from_orm
from integration_service.database.exceptions import (
    DataStoreDeleteFailed,
    DataStoreNotFound,
    DataStoreUpdateFailed,
    DataStoreCreateFailed,
    DataStoreGetFailed,
    SecretsCreateFailed,
    SecretsGetFailed,
    KekKidGetFailed,
    CertCreateFailed,
    CertGetFailed
)
from integration_service.database.models import DataStoreORM, SecretORM, CertORM
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.encryptor.models.cert import Cert


logger = logging.getLogger(__name__)


class DataStoreRepository:
    def __init__(self, backend_connector: DatabaseBackendConnector) -> None:
        self._db = backend_connector

    async def get_user_datastore_ids(self, user_id: UUID, organization_id: UUID) -> List[UUID]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(DataStoreORM.id)
                    .where(DataStoreORM.organization_id == organization_id)
                    .where(DataStoreORM.user_id == user_id))
                
                return [row[0] for row in result.all()]
        except SQLAlchemyError as e:
            msg = f'Get datastore IDs failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreGetFailed(msg) from e

    async def get_datastore(self, user_id: UUID, organization_id: UUID, datastore_id: UUID) -> DataStore:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(DataStoreORM)
                    .where(DataStoreORM.organization_id == organization_id)
                    .where(DataStoreORM.user_id == user_id)
                    .where(DataStoreORM.id == datastore_id)
                )
                datastore = result.scalar_one_or_none()
                if datastore is None:
                    raise DataStoreNotFound(f'No datastore found for ID: {datastore_id}')
                return datastore_from_orm(datastore)
        except SQLAlchemyError as e:
            msg = f'Get datastore {datastore_id} failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreGetFailed(msg) from e
        
    async def get_datastore_by_id(self, user_id: UUID, organization_id: UUID, datastore_id: UUID) -> DataStore:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(DataStoreORM)
                    .where(DataStoreORM.id == datastore_id)
                )
                datastore = result.scalar_one_or_none()
                if datastore is None:
                    raise DataStoreNotFound(f'No datastore found for ID: {datastore_id}')
                return datastore_from_orm(datastore)
        except SQLAlchemyError as e:
            msg = f'Get datastore by ID failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreGetFailed(msg) from e

    async def create_datastore(
            self,
            organization_id: UUID,
            user_id: UUID,
            datastore_create: DataStoreCreate
    ) -> UUID:
        try:
            datastore_orm = orm_from_datastore_create(
                organization_id=organization_id,
                user_id=user_id,
                datastore_create=datastore_create
            )
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add(datastore_orm)
                await scoped_session.flush()
                return datastore_orm.id
        except SQLAlchemyError as e:
            msg = f'Create datastore failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreCreateFailed(msg) from e
        
    async def delete_datastore(self, user_id: UUID, organization_id: UUID, datastore_id: UUID) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as active_session:
                stmt = (
                    delete(DataStoreORM)
                    .where(
                        DataStoreORM.id == datastore_id,
                        DataStoreORM.user_id == user_id,
                        DataStoreORM.organization_id == organization_id
                    )
                )
                result = await active_session.execute(stmt)
            if result.rowcount == 0:
                msg = f'Data store delete failed. Data store not found for data store id: {datastore_id}'
                raise DataStoreDeleteFailed(msg)
        except SQLAlchemyError as e:
            msg = f'Delete data store failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreDeleteFailed(msg) from e

    async def get_datastore_profiles(self, user_id: UUID, organization_id: UUID) -> List[DataStoreProfile]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(DataStoreORM).where(
                        DataStoreORM.user_id == user_id,
                        DataStoreORM.organization_id == organization_id
                    )
                )
                datastores = result.scalars().all()
                return [datastore_profile_from_orm(datastore) for datastore in datastores]
        except SQLAlchemyError as e:
            msg = f'Get data store profiles failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreGetFailed from e

    async def create_secrets(
            self,
            organization_id: UUID,
            user_id: UUID,
            secrets: Dict[SecretType, DataStoreSecret]
    ) -> None:
        try:
            secrets_orm = orm_from_secrets(secrets)
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add_all(secrets_orm)
                await scoped_session.flush()
        except SQLAlchemyError as e:
            msg = f'Create secrets failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise SecretsCreateFailed(e) from e
        
    async def get_secrets(
        self,
        organization_id: UUID,
        user_id: UUID,
        datastore_id: UUID
    ) -> Dict[SecretType, DataStoreSecret]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(SecretORM)
                    .where(SecretORM.organization_id == organization_id)
                    .where(SecretORM.user_id == user_id)
                    .where(SecretORM.datastore_id == datastore_id)
                )
                secrets = result.scalars().all()
                return secrets_from_orm(secrets)
        except SQLAlchemyError as e:
            msg = f'Get secrets failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise SecretsGetFailed(msg) from e

    async def get_kek_kid(self, datastore_id: UUID, user_id: UUID, organization_id: UUID) -> str:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(DataStoreORM.kek_kid)
                    .where(DataStoreORM.id == datastore_id)
                )
                kek_kid = result.scalar_one()
                return kek_kid
        except SQLAlchemyError as e:
            msg = f'Get kek_kid failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise KekKidGetFailed(msg) from e

    async def create_cert(
        self,
        organization_id: UUID,
        user_id: UUID,
        cert: Cert
    ) -> None:
        try:
            cert_orm = orm_from_cert(
                organization_id=organization_id,
                user_id=user_id,
                cert=cert
            )
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add(cert_orm)
                await scoped_session.flush()
        except SQLAlchemyError as e:
            msg = f'Create certificate failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise CertCreateFailed(msg) from e

    async def get_datastore_cert_profiles(
        self,
        organization_id: UUID,
        user_id: UUID
    ) -> List[CertProfile]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(CertORM)
                    .where(CertORM.organization_id == organization_id)
                    .where(CertORM.user_id == user_id)
                    .where(CertORM.state == CertState.pending.value)
                )
                certs = result.scalars().all()
                return [cert_profile_from_orm(cert) for cert in certs]
        except SQLAlchemyError as e:
            msg = f'Get certificate profiles failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise CertGetFailed(msg) from e

    async def update_datastore(
        self,
        datastore_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        datastore_update: DataStoreUpdate,
        secrets: Dict[SecretType, DataStoreSecret]
    ) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as active_session:
                await self._lock_datastore(active_session, datastore_id)
                await self._update_datastore(
                    active_session,
                    datastore_id,
                    user_id,
                    organization_id,
                    datastore_update
                )
                latest_version = await self._get_latest_secrets_version(active_session, datastore_id)
                new_version = latest_version + 1
                await self._insert_secrets(active_session, secrets, new_version)
                await active_session.flush()
        except SQLAlchemyError as e:
            msg = f'Update data store failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise DataStoreUpdateFailed(msg) from e

    async def _get_latest_secrets_version(self, active_session: AsyncSession, datastore_id: UUID) -> int:
        result = await active_session.execute(
            select(func.coalesce(func.max(SecretORM.version), 0))
            .where(SecretORM.datastore_id == datastore_id)
        )
        current_version = result.scalar_one()
        return current_version

    async def _lock_datastore(self, active_session: AsyncSession, datastore_id: UUID) -> None:
        u = datastore_id.int
        key = u & 0x7FFFFFFFFFFFFFFF
        await active_session.execute(
            text('SELECT pg_advisory_xact_lock(CAST(:k AS bigint))'),
            {'k': key},
        )

    async def _update_datastore(
        self,
        active_session: AsyncSession,
        datastore_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        datastore_update: DataStoreUpdate
    ) -> None:
        stmt = (
            update(DataStoreORM)
            .where(
                DataStoreORM.id == datastore_id,
                DataStoreORM.user_id == user_id,
                DataStoreORM.organization_id == organization_id
            )
            .values(**datastore_update.update_args)
        )
        result = await active_session.execute(stmt)
        if result.rowcount == 0:
            msg = f'Data store update failed: No data store found for ID {datastore_id}'
            raise DataStoreUpdateFailed(msg)


    async def _insert_secrets(
        self,
        active_session: AsyncSession,
        secrets: Dict[SecretType, DataStoreSecret],
        version: int
    ) -> None:
        secrets_orm = orm_from_secrets(secrets, version)
        active_session.add_all(secrets_orm)
