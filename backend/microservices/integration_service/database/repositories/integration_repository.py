from typing import List, Dict, Tuple
from uuid import UUID

from domain_models import IntegrationProfile
from utils.encryption import EncryptedIntegration
from shared.database.models import IntegrationORM
from shared.database.dependencies import backend_session_scope


class IntegrationUpdateFailed(Exception):
    pass


class IntegrationDeleteFailed(Exception):
    pass


class IntegrationRepository:
    def get_user_integration_ids(self, user_id: UUID, organization_id: UUID) -> List[UUID]:
        with backend_session_scope() as scoped_session:
            integrations_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(organization_id=organization_id, user_id=user_id)
                .all()
            )
            return [integration_orm.id for integration_orm in integrations_orm]
        
    def get_integration(self, user_id: UUID, organization_id: UUID, integration_id: str) -> EncryptedIntegration:
        with backend_session_scope() as scoped_session:
            integration_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(
                    organization_id=organization_id, 
                    user_id=user_id,
                    id=integration_id
                )
                .first()
            )
            return EncryptedIntegration(
                organization_id=integration_orm.organization_id,
                user_id=integration_orm.user_id,
                service_type=integration_orm.service_type,
                auth_method=integration_orm.auth_method,
                connection_name=integration_orm.connection_name,
                host=integration_orm.host,
                port=integration_orm.port,
                database_name=integration_orm.database_name,
                encrypted_username=integration_orm.encrypted_username,
                encrypted_password=integration_orm.encrypted_password,
                encrypted_kerberos_principal=integration_orm.encrypted_kerberos_principal,
                encrypted_windows_domain=integration_orm.encrypted_windows_domain,
                encrypted_extra_options=integration_orm.encrypted_extra_options,
                autosync_on=integration_orm.autosync_on
            )
        
    def get_integration_by_id(self, integration_id: UUID) -> EncryptedIntegration:
        with backend_session_scope() as scoped_session:
            integration_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(
                    id=integration_id
                )
                .first()
            )
            return EncryptedIntegration(
                organization_id=integration_orm.organization_id,
                user_id=integration_orm.user_id,
                service_type=integration_orm.service_type,
                auth_method=integration_orm.auth_method,
                connection_name=integration_orm.connection_name,
                host=integration_orm.host,
                port=integration_orm.port,
                database_name=integration_orm.database_name,
                encrypted_username=integration_orm.encrypted_username,
                encrypted_password=integration_orm.encrypted_password,
                encrypted_kerberos_principal=integration_orm.encrypted_kerberos_principal,
                encrypted_windows_domain=integration_orm.encrypted_windows_domain,
                encrypted_extra_options=integration_orm.encrypted_extra_options,
                autosync_on=integration_orm.autosync_on
            )
        
    def create_integration(self, encrypted_integration: EncryptedIntegration) -> Tuple[str, UUID]:
        with backend_session_scope() as scoped_session:
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
            scoped_session.flush()
            integration_id = integration_orm.id
        return integration_id
        
    def update_integration(self, integration_id: UUID, user_id: UUID, organization_id: UUID, update_args: Dict[str, str | bool | int]) -> None:
        with backend_session_scope() as active_session:
            result = active_session.query(IntegrationORM).filter_by(
                id=integration_id,
                organization_id=organization_id,
                user_id=user_id
            ).update(update_args)

            if result == 0:
                raise IntegrationUpdateFailed(f'Integration update failed. Integration not found for integration id: {integration_id}')
        
    def delete_integration(self, user_id: UUID, organization_id: UUID, integration_id: str) -> None:
        with backend_session_scope() as active_session:
            result = active_session.query(IntegrationORM).filter_by(
                    id=integration_id,
                    organization_id=organization_id,
                    user_id=user_id
                ).delete()
            
            if result == 0:
                raise IntegrationDeleteFailed(f'Integration delete failed. Integration not found for integration id: {integration_id}')

    def get_user_integration_profiles(self, user_id: UUID, organization_id: UUID) -> List[IntegrationProfile]:
        with backend_session_scope() as scoped_session:
            integrations_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(organization_id=organization_id, user_id=user_id)
            )

            return [
                IntegrationProfile(
                    id=integration.id,
                    service_type=integration.service_type,
                    connection_name=integration.connection_name,
                    database_name=integration.database_name,
                    auth_method=integration.auth_method,
                    autosync_on=integration.autosync_on
                )
                for integration in integrations_orm
            ]