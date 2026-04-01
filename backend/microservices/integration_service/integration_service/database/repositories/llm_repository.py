import logging
from uuid import UUID
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from integration_service.database.exceptions import UserLlmCreateFailed, UserLlmGetFailed
from integration_service.database.models import UserLlmORM
from integration_service.domain.mappers.user_llm.converter import (
    orm_from_user_llm,
    user_llm_profile_from_orm,
    user_llm_from_orm
)
from integration_service.domain.models.user_llm import UserLlm, UserLlmProfile

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector

logger = logging.getLogger(__file__)


class LlmRepository:
    def __init__(self, backend_connector: DatabaseBackendConnector) -> None:
        self._db = backend_connector

    async def create_user_llm(
        self,
        organization_id: UUID,
        user_id: UUID,
        user_llm: UserLlm,
    ) -> UUID:
        try:
            model_orm = orm_from_user_llm(
                organization_id=organization_id,
                user_id=user_id,
                user_llm=user_llm
            )

            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                scoped_session.add(model_orm)
                await scoped_session.flush()
                return model_orm.id
        except SQLAlchemyError as e:
            msg = f'Create llm failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserLlmCreateFailed(msg) from e

    async def get_user_llm_profiles(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> List[UserLlmProfile]:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(UserLlmORM).where(
                        UserLlmORM.user_id == user_id,
                        UserLlmORM.organization_id == organization_id
                    )
                )
                user_llm_orms = result.scalars().all()
                return [user_llm_profile_from_orm(llm) for llm in user_llm_orms]
        except SQLAlchemyError as e:
            msg = f'Get user llm profiles failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserLlmGetFailed(msg) from e

    async def get_user_llm(
            self,
            organization_id: UUID,
            user_id: UUID,
            model_ref_id: UUID,
    ) -> UserLlm:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                result = await scoped_session.execute(
                    select(UserLlmORM).where(
                        UserLlmORM.user_id == user_id,
                        UserLlmORM.organization_id == organization_id,
                        UserLlmORM.id == model_ref_id,
                    )
                )
                user_llm_orm = result.scalar_one()
                return user_llm_from_orm(
                    organization_id=organization_id,
                    user_id=user_id,
                    user_llm_orm=user_llm_orm
                )
        except SQLAlchemyError as e:
            msg = f'Get user llms failed with database error: {str(e)}'
            logger.error(msg, exc_info=True)
            raise UserLlmGetFailed(msg) from e

