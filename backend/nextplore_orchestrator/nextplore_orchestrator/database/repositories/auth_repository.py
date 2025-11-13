import logging
from uuid import UUID
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from nextplore_orchestrator.database.exceptions import (
    OrganizationCreateFailed, 
    UserCreateFailed,
    OrganizationGetFailed,
    UserGetFailed,
    KekIdGetFailed,
    KekIdNotFound
)
from nextplore_orchestrator.database.models import OrganizationORM, UserORM
from nextplore_orchestrator.domain.models import Organization, User
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self, db_connector: DatabaseBackendConnector) -> None:
        self._db = db_connector

    async def get_org(self, azure_tenant_id: str) -> Optional[UUID]:
        try:
            async with self._db.session_scope() as scoped_session:
                result = await scoped_session.execute(
                    select(OrganizationORM)
                    .where(OrganizationORM.azure_tenant_id == azure_tenant_id)
                )
                organization_orm = result.scalar_one_or_none()
                return organization_orm.id
        except SQLAlchemyError as e:
            msg = f'Get organization failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OrganizationGetFailed(msg) from e

    async def create_org(self, organization: Organization, kek_kid: str) -> UUID:
        try:
            async with self._db.session_scope() as scoped_session:
                organization_orm = OrganizationORM(
                    azure_tenant_id=organization.azure_tenant_id,
                    name=organization.name,
                    domain=organization.domain,
                    kek_kid=kek_kid,
                    plan=organization.plan
                )
                scoped_session.add(organization_orm)
                scoped_session.flush()
                return organization_orm.id
        except SQLAlchemyError as e:
            msg = f'Create organization failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OrganizationCreateFailed(msg) from e
        
    async def get_user(self, user: User) -> Optional[UUID]:
        try:
            async with self._db.session_scope() as scoped_session:
                result = await scoped_session.execute(
                    select(UserORM)
                    .where(UserORM.azure_user_id == user.azure_user_id)
                    .where(UserORM.organization_id == user.organization_id)
                )
                user_orm = result.scalar_one_or_none()
                return user_orm.id
        except SQLAlchemyError as e:
            msg = f'Get user failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserGetFailed(msg) from e

    async def create_user(self, user: User) -> UUID:
        try:
            async with self._db.session_scope() as scoped_session:
                result = await scoped_session.execute(
                    select(UserORM)
                    .where(UserORM.azure_user_id == user.azure_user_id)
                    .where(UserORM.organization_id == user.organization_id)
                )
                user_orm = result.scalar_one_or_none()
                if not user_orm:
                    user_orm = UserORM(
                        azure_user_id=user.azure_user_id,
                        email=user.email,
                        name=user.name,
                        organization_id=user.organization_id,
                        sub=user.sub,
                        role=user.role
                    )
                    scoped_session.add(user_orm)
                    scoped_session.flush()
                    return user_orm.id
        except SQLAlchemyError as e:
            msg = f'Create user failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserCreateFailed(msg) from e
        
    async def get_kek_kid(self, organization_id: UUID) -> str:
        try:
            async with self._db.session_scope() as scoped_session:
                result = await scoped_session.execute(
                    select(OrganizationORM.kek_kid)
                    .where(OrganizationORM.id == organization_id)
                )
                kek_id = result.scalar()
        except SQLAlchemyError as e:
            msg = f'Get Kek ID failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise KekIdGetFailed(msg) from e

        if not kek_id:
            raise KekIdNotFound(f'Kek ID not found for organization: {organization_id}')
        return kek_id
