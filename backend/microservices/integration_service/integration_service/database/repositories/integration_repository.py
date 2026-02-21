import logging
from typing import List, Dict
from uuid import UUID
from dataclasses import asdict
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from svc_integration_contracts.models import CertState

from integration_service.domain.models.integration import (
    IntegrationUpdate,
    IntegrationCreate,
    IntegrationProfile,
    Integration
)
from integration_service.domain.models.secret import IntegrationSecret, SecretType
from integration_service.domain.models.cert import CertProfile
from integration_service.domain.mappers.integration import (
    orm_from_integration_create,
    integration_profile_from_orm,
    integration_from_orm
)
from integration_service.domain.mappers.secret import orm_from_secrets, secrets_from_orm
from integration_service.domain.mappers.cert import orm_from_cert, cert_profile_from_orm
from integration_service.database.exceptions import (
    IntegrationDeleteFailed, 
    IntegrationNotFound, 
    IntegrationUpdateFailed,
    IntegrationCreateFailed,
    IntegrationGetFailed,
    SecretsCreateFailed,
    SecretsGetFailed,
    KekKidGetFailed,
    CertCreateFailed,
    CertGetFailed
)
from integration_service.database.models import IntegrationORM, SecretORM, CertORM
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.encryptor.models.cert import Cert


logger = logging.getLogger(__name__)


class IntegrationRepository:
    def __init__(self, backend_connector: DatabaseBackendConnector) -> None:
        self._db = backend_connector

    async def get_user_integration_ids(self, user_id: UUID, organization_id: UUID) -> List[UUID]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM.id)
                    .where(IntegrationORM.organization_id == organization_id)
                    .where(IntegrationORM.user_id == user_id))
                
                return [row[0] for row in result.all()]
        except SQLAlchemyError as e:
            msg = f'Get integration IDs failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationGetFailed(msg) from e

    async def get_integration(self, user_id: UUID, organization_id: UUID, integration_id: UUID) -> Integration:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM)
                    .where(IntegrationORM.organization_id == organization_id)
                    .where(IntegrationORM.user_id == user_id)
                    .where(IntegrationORM.id == integration_id)
                )
                integration = result.scalar_one_or_none()
                if integration is None:
                    raise IntegrationNotFound(f'No integration found for ID: {integration_id}')
                return integration_from_orm(integration)
        except SQLAlchemyError as e:
            msg = f'Get integration {integration_id} failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationGetFailed(msg) from e
        
    async def get_integration_by_id(self, user_id: UUID, organization_id: UUID, integration_id: UUID) -> Integration:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM)
                    .where(IntegrationORM.id == integration_id)
                )
                integration = result.scalar_one_or_none()
                if integration is None:
                    raise IntegrationNotFound(f'No integration found for ID: {integration_id}')
                return integration_from_orm(integration)
        except SQLAlchemyError as e:
            msg = f'Get integration by ID failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationGetFailed(msg) from e

    async def create_integration(
            self,
            organization_id: UUID,
            user_id: UUID,
            integration_create: IntegrationCreate
    ) -> UUID:
        try:
            integration_orm = orm_from_integration_create(
                organization_id=organization_id,
                user_id=user_id,
                integration_create=integration_create
            )
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add(integration_orm)
                await scoped_session.flush()
                return integration_orm.id
        except SQLAlchemyError as e:
            msg = f'Create integration failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationCreateFailed(msg) from e
        
    async def delete_integration(self, user_id: UUID, organization_id: UUID, integration_id: UUID) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as active_session:
                stmt = (
                    delete(IntegrationORM)
                    .where(
                        IntegrationORM.id == integration_id,
                        IntegrationORM.user_id == user_id,
                        IntegrationORM.organization_id == organization_id
                    )
                )
                result = await active_session.execute(stmt)
            if result.rowcount == 0:
                msg = f'Integration delete failed. Integration not found for integration id: {integration_id}'
                raise IntegrationDeleteFailed(msg)
        except SQLAlchemyError as e:
            msg = f'Delete integration failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationDeleteFailed(msg) from e

    async def get_integration_profiles(self, user_id: UUID, organization_id: UUID) -> List[IntegrationProfile]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM).where(
                        IntegrationORM.user_id == user_id,
                        IntegrationORM.organization_id == organization_id
                    )
                )
                integrations = result.scalars().all()
                return [integration_profile_from_orm(integration) for integration in integrations]
        except SQLAlchemyError as e:
            msg = f'Get integration profiles failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationGetFailed from e

    async def create_secrets(
            self,
            organization_id: UUID,
            user_id: UUID,
            secrets: Dict[SecretType, IntegrationSecret]
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
        integration_id: UUID
    ) -> Dict[SecretType, IntegrationSecret]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(SecretORM)
                    .where(SecretORM.organization_id == organization_id)
                    .where(SecretORM.user_id == user_id)
                    .where(SecretORM.integration_id == integration_id)
                )
                secrets = result.scalars().all()
                return secrets_from_orm(secrets)
        except SQLAlchemyError as e:
            msg = f'Get secrets failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise SecretsGetFailed(msg) from e

    async def get_kek_kid(self, integration_id: UUID, user_id: UUID, organization_id: UUID) -> str:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM.kek_kid)
                    .where(IntegrationORM.id == integration_id)
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

    async def get_cert_profiles(
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

    async def update_integration(
        self,
        integration_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        integration_update: IntegrationUpdate,
        secrets: Dict[SecretType, IntegrationSecret]
    ) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as active_session:
                await self._lock_integration(active_session, integration_id)
                await self._update_integration(
                    active_session,
                    integration_id,
                    user_id,
                    organization_id,
                    integration_update
                )
                latest_version = await self._get_latest_secrets_version(active_session, integration_id)
                new_version = latest_version + 1
                await self._insert_secrets(active_session, secrets, new_version)
                await active_session.flush()
        except SQLAlchemyError as e:
            msg = f'Update integration failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise IntegrationUpdateFailed(msg) from e

    async def _get_latest_secrets_version(self, active_session: AsyncSession, integration_id: UUID) -> int:
        result = await active_session.execute(
            select(func.coalesce(func.max(SecretORM.version), 0))
            .where(SecretORM.integration_id == integration_id)
        )
        current_version = result.scalar_one()
        return current_version

    async def _lock_integration(self, active_session: AsyncSession, integration_id: UUID) -> None:
        u = integration_id.int
        key1 = (u >> 64) & 0xFFFFFFFF
        key2 = u & 0xFFFFFFFF
        await active_session.execute(
            text('SELECT pg_advisory_xact_lock(:k1::int, :k2::int)'),
            {'k1': key1, 'k2': key2},
        )

    async def _update_integration(
        self,
        active_session: AsyncSession,
        integration_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        integration_update: IntegrationUpdate
    ) -> None:
        update_args = asdict(integration_update)
        stmt = (
            update(IntegrationORM)
            .where(
                IntegrationORM.id == integration_id,
                IntegrationORM.user_id == user_id,
                IntegrationORM.organization_id == organization_id
            )
            .values(**update_args)
        )
        result = await active_session.execute(stmt)
        if result.rowcount == 0:
            msg = f'Integration update failed: No integration found for ID {integration_id}'
            raise IntegrationUpdateFailed(msg)


    async def _insert_secrets(
        self,
        active_session: AsyncSession,
        secrets: Dict[SecretType, IntegrationSecret],
        version: int
    ) -> None:
        secrets_orm = orm_from_secrets(secrets, version)
        active_session.add_all(secrets_orm)
