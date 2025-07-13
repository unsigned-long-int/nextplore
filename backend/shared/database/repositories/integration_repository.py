from typing import List, Dict, Any
from uuid import UUID

from shared.database.models import IntegrationORM
from shared.identity_service import UserIdentity
from shared.database.connection_builder import (
    create_integration_metadata,
    IntegrationMetadata
)
from shared.database.dependencies import backend_session_scope


class IntegrationUpdateFailed(Exception):
    pass


class IntegrationDeleteFailed(Exception):
    pass


class IntegrationRepository:
    def get_user_integration_ids(self, user_identity: UserIdentity) -> List[UUID]:
        with backend_session_scope() as scoped_session:
            integrations_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(organization_id=user_identity.organization_id, user_id=user_identity.user_id)
                .all()
            )
            return [integration_orm.id for integration_orm in integrations_orm]
        
    def get_integration_metadata(self, user_identity: UserIdentity, integration_id: str) -> IntegrationMetadata:
        with backend_session_scope() as scoped_session:
            integration_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(
                    organization_id=user_identity.organization_id, 
                    user_id=user_identity.user_id,
                    id=integration_id
                )
                .first()
            )
            return create_integration_metadata(integration_orm)
        
    def get_user_integration_number(self, user_identity: UserIdentity) -> int:
        with backend_session_scope() as scoped_session:
            integration_number = (
                scoped_session.query(IntegrationORM)
                .filter_by(organization_id=user_identity.organization_id, user_id=user_identity.user_id)
                .count()
            )
            return integration_number
        
    def update_integration(self, user_identity: UserIdentity, integration_id: str, update_args: Dict[str, Any]) -> None:
        with backend_session_scope() as active_session:
            result = active_session.query(IntegrationORM).filter_by(
                id=integration_id,
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id
            ).update(update_args)

            if result == 0:
                raise IntegrationUpdateFailed(f'Integration update failed. Integration not found for integration id: {integration_id}')
        
    def delete_integration(self, user_identity: UserIdentity, integration_id: str) -> None:
        with backend_session_scope() as active_session:
            result = active_session.query(IntegrationORM).filter_by(
                    id=integration_id,
                    organization_id=user_identity.organization_id,
                    user_id=user_identity.user_id
                ).delete()
            
            if result == 0:
                raise IntegrationDeleteFailed(f'Integration delete failed. Integration not found for integration id: {integration_id}')
