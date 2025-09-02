import logging
from typing import List
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError

from database.exceptions import SecretsCreateFailed
from database.models import SecretORM
from domain_models import Secret
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector


logger = logging.getLogger(__name__)

class SecretRepository:
    def __init__(self, db_connector: DatabaseBackendConnector) -> None:
        self._db = db_connector

    async def create_secrets(self, organization_id: UUID, user_id: UUID, integration_id: UUID, secrets: List[Secret]) -> None:
        try:
            async with self._db.session_scope(organization_id, user_id) as scoped_session:
                secrets_orm = [
                    SecretORM(
                        id=s.id,
                        organization_id=organization_id,
                        user_id=user_id,
                        integration_id=integration_id,
                        ciphertext=s.ciphertext,
                        nonce=s.nonce,
                        tag=s.tag,
                        wrapped_dek=s.wrapped_dek,
                        kek_kid=s.kek_kid,
                        enc_alg=s.enc_alg,
                        wrap_alg=s.wrap_alg,
                        aad=s.aad,
                        encoding=s.encoding,
                        version=s.version
                    )
                    for s in secrets
                ]
                scoped_session.add_all(secrets_orm)
                await scoped_session.flush()
        except SQLAlchemyError as e:
            logger.error(f'Create secrets failed: {e}', exc_info=True)
            raise SecretsCreateFailed from e
        