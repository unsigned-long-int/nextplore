from typing import List, Dict
from uuid import UUID
from sqlalchemy import select, update, delete

from domain_models import IntegrationProfile
from utils.encryption import EncryptedIntegration
from shared.database.models import IntegrationORM
from shared.database.dependencies import DatabaseBackendConnector


class IntegrationUpdateFailed(Exception):
    pass


class IntegrationDeleteFailed(Exception):
    pass


class IntegrationNotFound(Exception):
    pass


class IntegrationRepository:
    def __init__(self) -> None:
        self.database_backend_connector = DatabaseBackendConnector()

    async def get_user_integration_ids(self, user_id: UUID, organization_id: UUID) -> List[UUID]:
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(IntegrationORM.id)
                .where(IntegrationORM.organization_id == organization_id)
                .where(IntegrationORM.user_id == user_id))
            
            return [row[0] for row in result.all()]
        
    async def get_integration(self, user_id: UUID, organization_id: UUID, integration_id: str) -> EncryptedIntegration:
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(IntegrationORM)
                .where(IntegrationORM.organization_id == organization_id)
                .where(IntegrationORM.user_id == user_id)
                .where(IntegrationORM.id == integration_id)
            )
            integration = result.scalar_one_or_none()
            if integration is None:
                raise IntegrationNotFound(f'No integration found for ID: {integration_id}')

            return self._to_encrypted_integration(integration)
        
    async def get_integration_by_id(self, integration_id: UUID) -> EncryptedIntegration:
        async with self.database_backend_connector.session_scope() as scoped_session:
            result = await scoped_session.execute(
                select(IntegrationORM)
                .where(IntegrationORM.id == integration_id)
            )
            integration = result.scalar_one_or_none()
            if integration is None:
                raise IntegrationNotFound(f'No integration found for ID: {integration_id}')

            return self._to_encrypted_integration(integration)
        
    async def create_integration(self, encrypted_integration: EncryptedIntegration) -> UUID:
        async with self.database_backend_connector.session_scope() as scoped_session:
            integration_orm = IntegrationORM(
                organization_id = encrypted_integration.organization_id,
                user_id = encrypted_integration.user_id,
                service_type = encrypted_integration.service_type,
                auth_method = encrypted_integration.auth_method,
                connection_name = encrypted_integration.connection_name,
                host = encrypted_integration.host,
                port = encrypted_integration.port,
                database_name = encrypted_integration.database_name,
                encrypted_username = encrypted_integration.encrypted_username,
                encrypted_password = encrypted_integration.encrypted_password,
                encrypted_kerberos_principal = encrypted_integration.encrypted_kerberos_principal,
                encrypted_windows_domain = encrypted_integration.encrypted_windows_domain,
                encrypted_extra_options = encrypted_integration.encrypted_extra_options,
                autosync_on=encrypted_integration.autosync_on
            )
            scoped_session.add(integration_orm)
            await scoped_session.flush()
            return integration_orm.id
        
    async def update_integration(self, integration_id: UUID, user_id: UUID, organization_id: UUID, update_args: Dict[str, str | bool | int]) -> None:
        async with self.database_backend_connector.session_scope() as active_session:
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
        
    async def delete_integration(self, user_id: UUID, organization_id: UUID, integration_id: str) -> None:
        async with self.database_backend_connector.session_scope() as active_session:
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

    async def get_user_integration_profiles(self, user_id: UUID, organization_id: UUID) -> List[IntegrationProfile]:
        async with self.database_backend_connector.session_scope() as scoped_session:
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