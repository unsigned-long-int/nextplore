import unittest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from svc_integration_contracts.models import Auth, DB, Cloud, CertState

from integration_service.database.repositories import IntegrationRepository
from integration_service.domain.models.integration import (
    IntegrationUpdate,
    IntegrationCreate,
    IntegrationProfile,
    Integration
)
from integration_service.domain.models.secret import IntegrationSecret, SecretType
from integration_service.domain.models.cert import CertProfile
from integration_service.database.exceptions import (
    IntegrationDeleteFailed,
    IntegrationNotFound,
    IntegrationUpdateFailed,
    IntegrationCreateFailed,
    IntegrationGetFailed,
    SecretsCreateFailed,
    SecretsGetFailed,
    SecretsVersionGetFailed,
    CertCreateFailed,
    CertGetFailed
)
from nextplore_sdk.encryptor.models.cert import Cert


class TestIntegrationRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.backend_connector_mock = MagicMock()
        self.session_mock = AsyncMock()
        self.backend_connector_mock.session_scope.return_value.__aenter__.return_value = self.session_mock

        self.repository = IntegrationRepository(backend_connector=self.backend_connector_mock)

        self.user_id = uuid4()
        self.organization_id = uuid4()
        self.integration_id = uuid4()

    async def test_get_user_integration_ids_returns_list_of_ids(self):
        integration_ids = [uuid4(), uuid4(), uuid4()]

        result_mock = MagicMock()
        result_mock.all.return_value = [(id,) for id in integration_ids]
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_user_integration_ids(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, integration_ids)
        self.session_mock.execute.assert_awaited_once()

    async def test_get_user_integration_ids_returns_empty_list(self):
        result_mock = MagicMock()
        result_mock.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_user_integration_ids(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, [])

    async def test_get_user_integration_ids_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(IntegrationGetFailed) as context:
            await self.repository.get_user_integration_ids(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

        self.assertIn('Get integration IDs failed', str(context.exception))

    @patch('integration_service.database.repositories.integration_repository.integration_from_orm')
    async def test_get_integration_returns_integration(self, integration_from_orm_mock):
        integration_orm_mock = MagicMock()
        expected_integration = Integration(
            id=self.integration_id,
            auth=Auth.password_proxy,
            cloud=Cloud.gcp,
            db=DB.postgresql,
            connection_name='test-connection',
            database_name='testdb',
            host='localhost',
            port=5432,
            autosync_on=True,
            organization_id=self.organization_id,
            user_id=self.user_id,
            kek_kid='kek_kid'
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = integration_orm_mock
        self.session_mock.execute.return_value = result_mock

        integration_from_orm_mock.return_value = expected_integration

        result = await self.repository.get_integration(
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_id=self.integration_id
        )

        self.assertEqual(result, expected_integration)
        integration_from_orm_mock.assert_called_once_with(integration_orm_mock)

    async def test_get_integration_raises_not_found_when_none(self):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session_mock.execute.return_value = result_mock

        with self.assertRaises(IntegrationNotFound) as context:
            await self.repository.get_integration(
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_id=self.integration_id
            )

        self.assertIn('No integration found', str(context.exception))

    async def test_get_integration_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(IntegrationGetFailed) as context:
            await self.repository.get_integration(
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_id=self.integration_id
            )

        self.assertIn('Get integration', str(context.exception))

    @patch('integration_service.database.repositories.integration_repository.integration_from_orm')
    async def test_get_integration_by_id_returns_integration(self, integration_from_orm_mock):
        integration_orm_mock = MagicMock()
        expected_integration = Integration(
            id=self.integration_id,
            organization_id=self.organization_id,
            user_id=self.user_id,
            kek_kid='kek_kid',
            auth=Auth.iam,
            cloud=Cloud.gcp,
            db=DB.postgresql,
            connection_name='test-connection',
            database_name='testdb',
            host='localhost',
            port=5432,
            autosync_on=True
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = integration_orm_mock
        self.session_mock.execute.return_value = result_mock

        integration_from_orm_mock.return_value = expected_integration

        result = await self.repository.get_integration_by_id(
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_id=self.integration_id
        )

        self.assertEqual(result, expected_integration)

    async def test_get_integration_by_id_raises_not_found_when_none(self):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session_mock.execute.return_value = result_mock

        with self.assertRaises(IntegrationNotFound):
            await self.repository.get_integration_by_id(
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_id=self.integration_id
            )

    @patch('integration_service.database.repositories.integration_repository.orm_from_integration_create')
    async def test_create_integration_returns_integration_id(self, orm_from_integration_create_mock):
        integration_create = IntegrationCreate(
            auth=Auth.iam,
            cloud=Cloud.snowflake_managed,
            db=DB.snowflake,
            connection_name='test-connection',
            database_name='testdb',
            host='localhost',
            port=5432,
            kek_kid='kek_kid',
        )

        integration_orm_mock = MagicMock()
        integration_orm_mock.id = self.integration_id
        orm_from_integration_create_mock.return_value = integration_orm_mock

        result = await self.repository.create_integration(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_create=integration_create
        )

        self.assertEqual(result, self.integration_id)
        self.session_mock.add.assert_called_once_with(integration_orm_mock)
        self.session_mock.flush.assert_awaited_once()

    @patch('integration_service.database.repositories.integration_repository.orm_from_integration_create')
    async def test_create_integration_raises_exception_on_database_error(self, orm_from_integration_create_mock):
        integration_create = IntegrationCreate(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.sqlserver,
            connection_name='test-connection',
            database_name='testdb',
            host='localhost',
            port=5432,
            kek_kid='kek_kid'
        )

        integration_orm_mock = MagicMock()
        orm_from_integration_create_mock.return_value = integration_orm_mock

        self.session_mock.flush.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(IntegrationCreateFailed) as context:
            await self.repository.create_integration(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_create=integration_create
            )

        self.assertIn('Create integration failed', str(context.exception))

    async def test_delete_integration_succeeds(self):
        result_mock = MagicMock()
        result_mock.rowcount = 1
        self.session_mock.execute.return_value = result_mock

        await self.repository.delete_integration(
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_id=self.integration_id
        )

        self.session_mock.execute.assert_awaited_once()

    async def test_delete_integration_raises_exception_when_not_found(self):
        result_mock = MagicMock()
        result_mock.rowcount = 0
        self.session_mock.execute.return_value = result_mock

        with self.assertRaises(IntegrationDeleteFailed) as context:
            await self.repository.delete_integration(
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_id=self.integration_id
            )

        self.assertIn('Integration not found', str(context.exception))

    async def test_delete_integration_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(IntegrationDeleteFailed) as context:
            await self.repository.delete_integration(
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_id=self.integration_id
            )

        self.assertIn('Delete integration failed', str(context.exception))

    @patch('integration_service.database.repositories.integration_repository.integration_profile_from_orm')
    async def test_get_integration_profiles_returns_list(self, integration_profile_from_orm_mock):
        integration_orm_1 = MagicMock()
        integration_orm_2 = MagicMock()

        profile_1 = IntegrationProfile(
            id=uuid4(),
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.mysql,
            connection_name='connection1',
            database_name='db1',
            host='localhost',
            port=5432,
            autosync_on=True
        )
        profile_2 = IntegrationProfile(
            id=uuid4(),
            auth=Auth.password_native,
            cloud=Cloud.azure,
            db=DB.sqlserver,
            connection_name='connection2',
            database_name='db2',
            host='localhost',
            port=3306,
            autosync_on=False
        )

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [integration_orm_1, integration_orm_2]
        self.session_mock.execute.return_value = result_mock

        integration_profile_from_orm_mock.side_effect = [profile_1, profile_2]

        result = await self.repository.get_integration_profiles(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], profile_1)
        self.assertEqual(result[1], profile_2)

    async def test_get_integration_profiles_returns_empty_list(self):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_integration_profiles(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, [])

    async def test_get_integration_profiles_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(IntegrationGetFailed):
            await self.repository.get_integration_profiles(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

    @patch('integration_service.database.repositories.integration_repository.orm_from_secrets')
    async def test_create_secrets_succeeds(self, orm_from_secrets_mock):
        secrets = {
            SecretType.PASSWORD: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        orm_from_secrets_mock.return_value = secrets_orm

        await self.repository.create_secrets(
            organization_id=self.organization_id,
            user_id=self.user_id,
            secrets=secrets
        )

        self.session_mock.add_all.assert_called_once_with(secrets_orm)
        self.session_mock.flush.assert_awaited_once()

    @patch('integration_service.database.repositories.integration_repository.orm_from_secrets')
    async def test_create_secrets_raises_exception_on_database_error(self, orm_from_secrets_mock):
        secrets = {
            SecretType.PASSWORD: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        orm_from_secrets_mock.return_value = secrets_orm

        self.session_mock.flush.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(SecretsCreateFailed):
            await self.repository.create_secrets(
                organization_id=self.organization_id,
                user_id=self.user_id,
                secrets=secrets
            )

    @patch('integration_service.database.repositories.integration_repository.secrets_from_orm')
    async def test_get_secrets_returns_secrets_dict(self, secrets_from_orm_mock):
        expected_secrets = {
            SecretType.PASSWORD: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = secrets_orm
        self.session_mock.execute.return_value = result_mock

        secrets_from_orm_mock.return_value = expected_secrets

        result = await self.repository.get_secrets(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_id=self.integration_id
        )

        self.assertEqual(result, expected_secrets)
        secrets_from_orm_mock.assert_called_once_with(secrets_orm)

    async def test_get_secrets_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(SecretsGetFailed):
            await self.repository.get_secrets(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id
            )

    async def test_get_latest_version_returns_version(self):
        expected_version = 5

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = expected_version
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_latest_version(
            integration_id=self.integration_id,
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, expected_version)

    async def test_get_latest_version_returns_one_when_no_secrets(self):
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 1
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_latest_version(
            integration_id=self.integration_id,
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, 1)

    async def test_get_latest_version_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(SecretsVersionGetFailed):
            await self.repository.get_latest_version(
                integration_id=self.integration_id,
                user_id=self.user_id,
                organization_id=self.organization_id
            )

    @patch('integration_service.database.repositories.integration_repository.orm_from_cert')
    async def test_create_cert_succeeds(self, orm_from_cert_mock):
        cert = Cert(
            cert_kid='cert-kid-123',
            cert_name='test-cert',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint123',
            not_before=datetime.utcnow(),
            not_after=datetime.utcnow()
        )

        cert_orm = MagicMock()
        orm_from_cert_mock.return_value = cert_orm

        await self.repository.create_cert(
            organization_id=self.organization_id,
            user_id=self.user_id,
            cert=cert
        )

        orm_from_cert_mock.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            cert=cert
        )
        self.session_mock.add.assert_called_once_with(cert_orm)
        self.session_mock.flush.assert_awaited_once()

    @patch('integration_service.database.repositories.integration_repository.orm_from_cert')
    async def test_create_cert_raises_exception_on_database_error(self, orm_from_cert_mock):
        cert = Cert(
            cert_kid='cert-kid-123',
            cert_name='test-cert',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint123',
            not_before=datetime.utcnow(),
            not_after=datetime.utcnow()
        )

        cert_orm = MagicMock()
        orm_from_cert_mock.return_value = cert_orm

        self.session_mock.flush.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(CertCreateFailed) as context:
            await self.repository.create_cert(
                organization_id=self.organization_id,
                user_id=self.user_id,
                cert=cert
            )

        self.assertIn('Create certificate failed', str(context.exception))

    @patch('integration_service.database.repositories.integration_repository.cert_profile_from_orm')
    async def test_get_cert_profiles_returns_list(self, cert_profile_from_orm_mock):
        cert_orm_1 = MagicMock()
        cert_orm_2 = MagicMock()

        now = datetime.utcnow()
        profile_1 = CertProfile(
            id=uuid4(),
            state=CertState.pending,
            cert_kid='cert-kid-1',
            cert_name='cert1',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint1',
            not_before=now,
            not_after=now,
            created_at=now
        )
        profile_2 = CertProfile(
            id=uuid4(),
            state=CertState.pending,
            cert_kid='cert-kid-2',
            cert_name='cert2',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint2',
            not_before=now,
            not_after=now,
            created_at=now
        )

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [cert_orm_1, cert_orm_2]
        self.session_mock.execute.return_value = result_mock

        cert_profile_from_orm_mock.side_effect = [profile_1, profile_2]

        result = await self.repository.get_cert_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], profile_1)
        self.assertEqual(result[1], profile_2)

    async def test_get_cert_profiles_returns_only_pending_certs(self):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_cert_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.assertEqual(result, [])
        self.session_mock.execute.assert_awaited_once()

    async def test_get_cert_profiles_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(CertGetFailed) as context:
            await self.repository.get_cert_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id
            )

        self.assertIn('Get certificate profiles failed', str(context.exception))

    @patch('integration_service.database.repositories.integration_repository.orm_from_secrets')
    async def test_update_integration_succeeds(self, orm_from_secrets_mock):
        integration_update = IntegrationUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {
            SecretType.PASSWORD: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        orm_from_secrets_mock.return_value = secrets_orm

        update_result_mock = MagicMock()
        update_result_mock.rowcount = 1
        self.session_mock.execute.return_value = update_result_mock

        await self.repository.update_integration(
            integration_id=self.integration_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_update=integration_update,
            secrets=secrets
        )

        self.session_mock.execute.assert_awaited()
        self.session_mock.add_all.assert_called_once_with(secrets_orm)
        self.session_mock.flush.assert_awaited_once()

    async def test_update_integration_raises_exception_when_not_found(self):
        integration_update = IntegrationUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {}

        update_result_mock = MagicMock()
        update_result_mock.rowcount = 0
        self.session_mock.execute.return_value = update_result_mock

        with self.assertRaises(IntegrationUpdateFailed) as context:
            await self.repository.update_integration(
                integration_id=self.integration_id,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_update=integration_update,
                secrets=secrets
            )

        self.assertIn('No integration found', str(context.exception))

    async def test_update_integration_raises_exception_on_database_error(self):
        integration_update = IntegrationUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {}

        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(IntegrationUpdateFailed) as context:
            await self.repository.update_integration(
                integration_id=self.integration_id,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_update=integration_update,
                secrets=secrets
            )

        self.assertIn('Update integration failed', str(context.exception))

    @patch('integration_service.database.repositories.integration_repository.orm_from_secrets')
    async def test_update_integration_updates_both_integration_and_secrets(self, orm_from_secrets_mock):
        integration_update = IntegrationUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {
            SecretType.PASSWORD: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        orm_from_secrets_mock.return_value = secrets_orm

        update_result_mock = MagicMock()
        update_result_mock.rowcount = 1
        self.session_mock.execute.return_value = update_result_mock

        await self.repository.update_integration(
            integration_id=self.integration_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_update=integration_update,
            secrets=secrets
        )

        self.session_mock.execute.assert_awaited_once()
        self.session_mock.add_all.assert_called_once_with(secrets_orm)
        self.session_mock.flush.assert_awaited_once()

    async def test_backend_connector_session_scope_called_correctly(self):
        result_mock = MagicMock()
        result_mock.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        await self.repository.get_user_integration_ids(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.backend_connector_mock.session_scope.assert_called_once_with(
            self.organization_id,
            self.user_id
        )