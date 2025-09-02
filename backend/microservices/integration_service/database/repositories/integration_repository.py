import logging
from typing import List, Dict
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError

from domain_models import IntegrationProfile, Integration
from utils.encryption import EncryptedIntegration
from database.exceptions import (
    IntegrationDeleteFailed, 
    IntegrationNotFound, 
    IntegrationUpdateFailed,
    IntegrationCreateFailed,
    IntegrationGetFailed
)
from database.models import IntegrationORM, IntegrationSecretMvORM
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)

class IntegrationRepository:
    def __init__(self, db_connector: DatabaseBackendConnector) -> None:
        self._db = db_connector

    async def get_user_integration_ids(self, user_id: UUID, organization_id: UUID) -> List[UUID]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM.id)
                    .where(IntegrationORM.organization_id == organization_id)
                    .where(IntegrationORM.user_id == user_id))
                
                return [row[0] for row in result.all()]
        except SQLAlchemyError as e:
            logger.error(f'Get integration ids failed: {e}', exc_info=True)
            raise IntegrationGetFailed from e
        
    async def get_integration_secret_mv(self, user_id: UUID, organization_id: UUID, integration_id: str) -> List[IntegrationSecretMvORM]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationSecretMvORM)
                    .where(IntegrationSecretMvORM.organization_id == organization_id)
                    .where(IntegrationSecretMvORM.user_id == user_id)
                    .where(IntegrationSecretMvORM.integration_id == integration_id)
                )
                integration_secrets = result.scalars().all()
                if not integration_secrets:
                    raise IntegrationNotFound(f'No integration found for ID: {integration_id}')

                return integration_secrets
        except SQLAlchemyError as e:
            logger.error(f'Get integration failed with database error: {e}', exc_info=True)
            raise IntegrationGetFailed from e
        
    async def get_integration_by_id(self, user_id: UUID, organization_id: UUID, integration_id: UUID) -> EncryptedIntegration:
        async with self._db.session_scope(organization_id, user_id) as scoped_session:
            result = await scoped_session.execute(
                select(IntegrationORM)
                .where(IntegrationORM.id == integration_id)
            )
            integration = result.scalar_one_or_none()
            if integration is None:
                raise IntegrationNotFound(f'No integration found for ID: {integration_id}')

            return self._to_encrypted_integration(integration)
        
    async def create_integration(self, organization_id: UUID, user_id: UUID, integration: Integration) -> UUID:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                integration_orm = IntegrationORM(
                    organization_id=organization_id,
                    user_id=user_id,
                    auth=integration.auth,
                    cloud=integration.cloud,
                    db=integration.db,
                    connection_name=integration.connection_name,
                    host=integration.host,
                    port=integration.port,
                    database_name=integration.database_name,
                    warehouse=integration.warehouse,
                    tenant_id=integration.tenant_id,
                    client_id=integration.client_id,
                    region=integration.region,
                    azure_cert_kid=integration.azure_cert_kid,
                    azure_public_key_pem=integration.azure_public_key_pem,
                    snowflake_public_key_pem=integration.snowflake_public_key_pem,
                    autosync_on=integration.autosync_on
                )
                scoped_session.add(integration_orm)
                await scoped_session.flush()
                return integration_orm.id
        except SQLAlchemyError as e:
            logger.error(f'Create integration failed with database error: {e}', exc_info=True)
            raise IntegrationCreateFailed from e
        
    async def update_integration(self, integration_id: UUID, user_id: UUID, organization_id: UUID, update_args: Dict[str, str | bool | int]) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as active_session:
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
                    raise IntegrationUpdateFailed(f'Integration update failed: No integration found for ID {integration_id}')
        except SQLAlchemyError as e:
            logger.error(f'Integration update failed with database error: {e}', exc_info=True)
            raise IntegrationUpdateFailed from e
        
    async def delete_integration(self, user_id: UUID, organization_id: UUID, integration_id: str) -> None:
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
                raise IntegrationDeleteFailed(f'Integration delete failed. Integration not found for integration id: {integration_id}')
        except SQLAlchemyError as e:
            logger.error(f'Delete integration failed with database error: {e}', exc_info=True)
            raise IntegrationDeleteFailed from e

    async def get_user_integration_profiles(self, user_id: UUID, organization_id: UUID) -> List[IntegrationProfile]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(IntegrationORM).where(
                        IntegrationORM.user_id == user_id,
                        IntegrationORM.organization_id == organization_id
                    )
                )
                integrations = result.scalars().all()
                return [
                    IntegrationProfile(
                        id=i.id,
                        service_type=i.service_type,
                        connection_name=i.connection_name,
                        database_name=i.database_name,
                        auth_method=i.auth_method,
                        autosync_on=i.autosync_on
                    )
                    for i in integrations
                ]
        except SQLAlchemyError as e:
            logger.error(f'Get integration failed with database error: {e}', exc_info=True)
            raise IntegrationGetFailed from e
        
    def _to_encrypted_integration(self, orm: IntegrationORM) -> EncryptedIntegration:
        return EncryptedIntegration(
            organization_id=orm.organization_id,
            user_id=orm.user_id,
            service_type=orm.service_type,
            auth_method=orm.auth_method,
            connection_name=orm.connection_name,
            host=orm.host,
            port=orm.port,
            database_name=orm.database_name,
            encrypted_username=orm.encrypted_username,
            encrypted_password=orm.encrypted_password,
            encrypted_kerberos_principal=orm.encrypted_kerberos_principal,
            encrypted_windows_domain=orm.encrypted_windows_domain,
            encrypted_extra_options=orm.encrypted_extra_options,
            autosync_on=orm.autosync_on
        )