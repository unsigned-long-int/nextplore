import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from nextplore_orchestrator.database.exceptions import (
    OrganizationCreateFailed, 
    UserCreateFailed,
    OrganizationGetFailed,
    UserGetFailed,
    KekIdGetFailed,
    KekIdNotFound,
    OnboardingRequestGetFailed,
    OnboardingRequestCreateFailed,
    OnboardingRequestDeleteFailed,
    OnboardingRequestUpdateFailed
)
from nextplore_orchestrator.domain.mappers import onboarding_request_from_orm, organization_from_orm
from nextplore_orchestrator.database.models import OrganizationORM, UserORM, OnboardingRequestORM
from nextplore_orchestrator.domain.models import Organization, User, OnboardingRequest


logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_org(self, azure_tenant_id: str) -> Optional[Organization]:
        try:
            result = await self._session.execute(
                select(OrganizationORM)
                .where(OrganizationORM.azure_tenant_id == azure_tenant_id)
            )
            organization_orm = result.scalar_one_or_none()
            if organization_orm:
                return organization_from_orm(organization_orm)
        except SQLAlchemyError as e:
            msg = f'Get organization failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OrganizationGetFailed(msg) from e

    async def create_org(self, organization: Organization, kek_kid: str) -> UUID:
        try:
            organization_orm = OrganizationORM(
                azure_tenant_id=organization.azure_tenant_id,
                name=organization.name,
                domain=organization.domain,
                kek_kid=kek_kid,
                plan=organization.plan,
                onboarding_request_id=organization.onboarding_request_id,
                activated_at=datetime.now(timezone.utc),
            )
            self._session.add(organization_orm)
            await self._session.flush()
            return organization_orm.id
        except SQLAlchemyError as e:
            msg = f'Create organization failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OrganizationCreateFailed(msg) from e
        
    async def get_user(self, user: User) -> Optional[UUID]:
        try:
            result = await self._session.execute(
                select(UserORM)
                .where(UserORM.azure_user_id == user.azure_user_id)
                .where(UserORM.organization_id == user.organization_id)
            )
            user_orm = result.scalar_one_or_none()
            return user_orm.id if user_orm else None
        except SQLAlchemyError as e:
            msg = f'Get user failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserGetFailed(msg) from e

    async def create_user(self, user: User) -> UUID:
        try:
            user_orm = UserORM(
                azure_user_id=user.azure_user_id,
                email=user.email,
                name=user.name,
                organization_id=user.organization_id,
                sub=user.sub,
                role=user.role
            )
            self._session.add(user_orm)
            await self._session.flush()
            return user_orm.id
        except SQLAlchemyError as e:
            msg = f'Create user failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserCreateFailed(msg) from e
        
    async def get_kek_kid(self, organization_id: UUID) -> str:
        try:
            result = await self._session.execute(
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

    async def get_onboarding_request_by_domain(self, email_domain: str) -> Optional[OnboardingRequest]:
        try:
            result = await self._session.execute(
                select(OnboardingRequestORM)
                .where(OnboardingRequestORM.domain == email_domain)
            )
            request_orm = result.scalar_one_or_none()
            if request_orm:
                return onboarding_request_from_orm(request_orm)
        except SQLAlchemyError as e:
            msg = f'Get onboarding request failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OnboardingRequestGetFailed(msg) from e

    async def create_onboarding_request(
        self,
        req: OnboardingRequest,
        outbox_mail_id: UUID,
        token: str,
        expires_at: datetime
    ) -> UUID:
        try:
            request_orm = OnboardingRequestORM(
                company_name=req.company_name,
                domain=req.email_domain,
                contact_email=req.contact_email,
                plan=req.plan,
                status=req.status,
                verification_token=token,
                outbox_mail_id=outbox_mail_id,
                verification_token_expires_at=expires_at
            )
            self._session.add(request_orm)
            await self._session.flush()
            return request_orm.id
        except SQLAlchemyError as e:
            msg = f'Create onboarding request failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OnboardingRequestCreateFailed(msg) from e

    async def delete_onboarding_request(self, onboarding_id: UUID) -> None:
        try:
            stmt = (
                delete(OnboardingRequestORM)
                .where(
                    OnboardingRequestORM.id == onboarding_id
                )
            )
            result = await self._session.execute(stmt)
            if result.rowcount == 0:
                msg = f'Onboarding request delete failed. Onboarding request not found for id: {onboarding_id}'
                raise OnboardingRequestDeleteFailed(msg)
        except SQLAlchemyError as e:
            msg = f'Delete onboarding request failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OnboardingRequestDeleteFailed(msg) from e

    async def get_onboarding_request_by_verification_token(self, token: str) -> Optional[OnboardingRequest]:
        try:
            result = await self._session.execute(
                select(OnboardingRequestORM)
                .where(OnboardingRequestORM.verification_token == token)
                .where(OnboardingRequestORM.verification_token_expires_at > datetime.now(timezone.utc))
            )
            request_orm = result.scalar_one_or_none()
            if request_orm:
                return onboarding_request_from_orm(request_orm)
        except SQLAlchemyError as e:
            msg = f'Get onboarding request failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OnboardingRequestGetFailed(msg) from e


    async def verify_email(self, request_id: UUID) -> None:
        try:
            stmt = (
                update(OnboardingRequestORM)
                .where(OnboardingRequestORM.id == request_id)
                .values({'email_verified': True, 'verified_at': datetime.now(timezone.utc)})
            )
            result = await self._session.execute(stmt)
            if result.rowcount == 0:
                msg = f'Verification failed: No onboarding request found for ID {request_id}'
                raise OnboardingRequestUpdateFailed(msg)
        except SQLAlchemyError as e:
            msg = f'Update onboarding request failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise OnboardingRequestUpdateFailed(msg) from e