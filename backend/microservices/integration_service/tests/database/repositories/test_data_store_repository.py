import unittest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from svc_integration_contracts.models import Auth, DB, Cloud, CertState

from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.models.datastore import (
    DataStoreUpdate,
    DataStoreCreate,
    DataStoreProfile,
    DataStore
)
from integration_service.domain.models.secret import DataStoreSecret, SecretType
from integration_service.domain.models.cert import CertProfile
from integration_service.database.exceptions import (
    DataStoreDeleteFailed,
    DataStoreNotFound,
    DataStoreUpdateFailed,
    DataStoreCreateFailed,
    DataStoreGetFailed,
    SecretsCreateFailed,
    SecretsGetFailed,
    KekKidGetFailed,
    CertCreateFailed,
    CertGetFailed
)
from nextplore_sdk.encryptor.models.cert import Cert


class TestDataStoreRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.backend_connector_mock = MagicMock()
        self.session_mock = AsyncMock()
        self.backend_connector_mock.session_scope.return_value.__aenter__.return_value = self.session_mock

        self.repository = DataStoreRepository(backend_connector=self.backend_connector_mock)

        self.user_id = uuid4()
        self.organization_id = uuid4()
        self.datastore_id = uuid4()

    async def test_get_user_datastore_ids_returns_list_of_ids(self):
        datastore_ids = [uuid4(), uuid4(), uuid4()]

        result_mock = MagicMock()
        result_mock.all.return_value = [(id,) for id in datastore_ids]
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_user_datastore_ids(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, datastore_ids)
        self.session_mock.execute.assert_awaited_once()

    async def test_get_user_datastore_ids_returns_empty_list(self):
        result_mock = MagicMock()
        result_mock.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_user_datastore_ids(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, [])

    async def test_get_user_datastore_ids_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(DataStoreGetFailed) as context:
            await self.repository.get_user_datastore_ids(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

        self.assertIn('Get datastore IDs failed', str(context.exception))

    @patch('integration_service.database.repositories.data_store_repository.datastore_from_orm')
    async def test_get_datastore_returns_datastore(self, datastore_from_orm_mock):
        datastore_orm_mock = MagicMock()
        expected_datastore = DataStore(
            id=self.datastore_id,
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
        result_mock.scalar_one_or_none.return_value = datastore_orm_mock
        self.session_mock.execute.return_value = result_mock

        datastore_from_orm_mock.return_value = expected_datastore

        result = await self.repository.get_datastore(
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_id=self.datastore_id
        )

        self.assertEqual(result, expected_datastore)
        datastore_from_orm_mock.assert_called_once_with(datastore_orm_mock)

    async def test_get_datastore_raises_not_found_when_none(self):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session_mock.execute.return_value = result_mock

        with self.assertRaises(DataStoreNotFound) as context:
            await self.repository.get_datastore(
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_id=self.datastore_id
            )

        self.assertIn('No datastore found', str(context.exception))

    async def test_get_datastore_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(DataStoreGetFailed) as context:
            await self.repository.get_datastore(
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_id=self.datastore_id
            )

        self.assertIn('Get datastore', str(context.exception))

    @patch('integration_service.database.repositories.data_store_repository.datastore_from_orm')
    async def test_get_datastore_by_id_returns_datastore(self, datastore_from_orm_mock):
        datastore_orm_mock = MagicMock()
        expected_datastore = DataStore(
            id=self.datastore_id,
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
        result_mock.scalar_one_or_none.return_value = datastore_orm_mock
        self.session_mock.execute.return_value = result_mock

        datastore_from_orm_mock.return_value = expected_datastore

        result = await self.repository.get_datastore_by_id(
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_id=self.datastore_id
        )

        self.assertEqual(result, expected_datastore)

    async def test_get_datastore_by_id_raises_not_found_when_none(self):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session_mock.execute.return_value = result_mock

        with self.assertRaises(DataStoreNotFound):
            await self.repository.get_datastore_by_id(
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_id=self.datastore_id
            )

    @patch('integration_service.database.repositories.data_store_repository.orm_from_datastore_create')
    async def test_create_datastore_returns_datastore_id(self, orm_from_datastore_create_mock):
        datastore_create = DataStoreCreate(
            auth=Auth.iam,
            cloud=Cloud.snowflake_managed,
            db=DB.snowflake,
            connection_name='test-connection',
            descr='test-descr',
            database_name='testdb',
            host='localhost',
            port=5432,
            kek_kid='kek_kid',
        )

        datastore_orm_mock = MagicMock()
        datastore_orm_mock.id = self.datastore_id
        orm_from_datastore_create_mock.return_value = datastore_orm_mock

        result = await self.repository.create_datastore(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_create=datastore_create
        )

        self.assertEqual(result, self.datastore_id)
        self.session_mock.add.assert_called_once_with(datastore_orm_mock)
        self.session_mock.flush.assert_awaited_once()

    @patch('integration_service.database.repositories.data_store_repository.orm_from_datastore_create')
    async def test_create_datastore_raises_exception_on_database_error(self, orm_from_datastore_create_mock):
        datastore_create = DataStoreCreate(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.sqlserver,
            connection_name='test-connection',
            descr='test-descr',
            database_name='testdb',
            host='localhost',
            port=5432,
            kek_kid='kek_kid'
        )

        datastore_orm_mock = MagicMock()
        orm_from_datastore_create_mock.return_value = datastore_orm_mock

        self.session_mock.flush.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(DataStoreCreateFailed) as context:
            await self.repository.create_datastore(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_create=datastore_create
            )

        self.assertIn('Create datastore failed', str(context.exception))

    async def test_delete_datastore_succeeds(self):
        result_mock = MagicMock()
        result_mock.rowcount = 1
        self.session_mock.execute.return_value = result_mock

        await self.repository.delete_datastore(
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_id=self.datastore_id
        )

        self.session_mock.execute.assert_awaited_once()

    async def test_delete_datastore_raises_exception_when_not_found(self):
        result_mock = MagicMock()
        result_mock.rowcount = 0
        self.session_mock.execute.return_value = result_mock

        with self.assertRaises(DataStoreDeleteFailed) as context:
            await self.repository.delete_datastore(
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_id=self.datastore_id
            )

        self.assertIn('Data store not found', str(context.exception))

    async def test_delete_datastore_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(DataStoreDeleteFailed) as context:
            await self.repository.delete_datastore(
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_id=self.datastore_id
            )

        self.assertIn('Delete data store failed', str(context.exception))

    @patch('integration_service.database.repositories.data_store_repository.datastore_profile_from_orm')
    async def test_get_datastore_profiles_returns_list(self, datastore_profile_from_orm_mock):
        datastore_orm_1 = MagicMock()
        datastore_orm_2 = MagicMock()

        profile_1 = DataStoreProfile(
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
        profile_2 = DataStoreProfile(
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
        result_mock.scalars.return_value.all.return_value = [datastore_orm_1, datastore_orm_2]
        self.session_mock.execute.return_value = result_mock

        datastore_profile_from_orm_mock.side_effect = [profile_1, profile_2]

        result = await self.repository.get_datastore_profiles(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], profile_1)
        self.assertEqual(result[1], profile_2)

    async def test_get_datastore_profiles_returns_empty_list(self):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_datastore_profiles(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, [])

    async def test_get_datastore_profiles_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(DataStoreGetFailed):
            await self.repository.get_datastore_profiles(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

    @patch('integration_service.database.repositories.data_store_repository.orm_from_secrets')
    async def test_create_secrets_succeeds(self, orm_from_secrets_mock):
        secrets = {
            SecretType.PASSWORD: DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
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

    @patch('integration_service.database.repositories.data_store_repository.orm_from_secrets')
    async def test_create_secrets_raises_exception_on_database_error(self, orm_from_secrets_mock):
        secrets = {
            SecretType.PASSWORD: DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
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

    @patch('integration_service.database.repositories.data_store_repository.secrets_from_orm')
    async def test_get_secrets_returns_secrets_dict(self, secrets_from_orm_mock):
        expected_secrets = {
            SecretType.PASSWORD: DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
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
            datastore_id=self.datastore_id
        )

        self.assertEqual(result, expected_secrets)
        secrets_from_orm_mock.assert_called_once_with(secrets_orm)

    async def test_get_secrets_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(SecretsGetFailed):
            await self.repository.get_secrets(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id
            )

    async def test_get_kek_kid_returns_kek_kid(self):
        expected_kek_kid = 'kek-kid-12345'

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = expected_kek_kid
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_kek_kid(
            datastore_id=self.datastore_id,
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.assertEqual(result, expected_kek_kid)
        self.session_mock.execute.assert_awaited_once()

    async def test_get_kek_kid_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(KekKidGetFailed) as context:
            await self.repository.get_kek_kid(
                datastore_id=self.datastore_id,
                user_id=self.user_id,
                organization_id=self.organization_id
            )

        self.assertIn('Get kek_kid failed', str(context.exception))

    @patch('integration_service.database.repositories.data_store_repository.orm_from_cert')
    async def test_create_cert_succeeds(self, orm_from_cert_mock):
        cert = Cert(
            cert_kid='cert-kid-123',
            cert_name='test-cert',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint123',
            not_before=datetime.now(timezone.utc),
            not_after=datetime.now(timezone.utc)
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

    @patch('integration_service.database.repositories.data_store_repository.orm_from_cert')
    async def test_create_cert_raises_exception_on_database_error(self, orm_from_cert_mock):
        cert = Cert(
            cert_kid='cert-kid-123',
            cert_name='test-cert',
            public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
            thumbprint_sha256='thumbprint123',
            not_before=datetime.now(timezone.utc),
            not_after=datetime.now(timezone.utc)
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

    @patch('integration_service.database.repositories.data_store_repository.cert_profile_from_orm')
    async def test_get_datastore_cert_profiles_returns_list(self, cert_profile_from_orm_mock):
        cert_orm_1 = MagicMock()
        cert_orm_2 = MagicMock()

        now = datetime.now(timezone.utc)
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

        result = await self.repository.get_datastore_cert_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], profile_1)
        self.assertEqual(result[1], profile_2)

    async def test_get_datastore_cert_profiles_returns_only_pending_certs(self):
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        result = await self.repository.get_datastore_cert_profiles(
            organization_id=self.organization_id,
            user_id=self.user_id
        )

        self.assertEqual(result, [])
        self.session_mock.execute.assert_awaited_once()

    async def test_get_datastore_cert_profiles_raises_exception_on_database_error(self):
        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(CertGetFailed) as context:
            await self.repository.get_datastore_cert_profiles(
                organization_id=self.organization_id,
                user_id=self.user_id
            )

        self.assertIn('Get certificate profiles failed', str(context.exception))

    @patch('integration_service.database.repositories.data_store_repository.orm_from_secrets')
    async def test_update_datastore_succeeds(self, orm_from_secrets_mock):
        datastore_update = DataStoreUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {
            SecretType.PASSWORD: DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        orm_from_secrets_mock.return_value = secrets_orm

        lock_result_mock = MagicMock()

        version_result_mock = MagicMock()
        version_result_mock.scalar_one.return_value = 5

        update_result_mock = MagicMock()
        update_result_mock.rowcount = 1

        self.session_mock.execute.side_effect = [
            lock_result_mock,
            update_result_mock,
            version_result_mock
        ]

        await self.repository.update_datastore(
            datastore_id=self.datastore_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_update=datastore_update,
            secrets=secrets
        )

        self.assertEqual(self.session_mock.execute.await_count, 3)

        orm_from_secrets_mock.assert_called_once_with(secrets, 6)
        self.session_mock.add_all.assert_called_once_with(secrets_orm)
        self.session_mock.flush.assert_awaited_once()

    async def test_update_datastore_raises_exception_when_not_found(self):
        datastore_update = DataStoreUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {}

        lock_result_mock = MagicMock()

        update_result_mock = MagicMock()
        update_result_mock.rowcount = 0

        self.session_mock.execute.side_effect = [
            lock_result_mock,
            update_result_mock
        ]

        with self.assertRaises(DataStoreUpdateFailed) as context:
            await self.repository.update_datastore(
                datastore_id=self.datastore_id,
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_update=datastore_update,
                secrets=secrets
            )

        self.assertIn('No data store found', str(context.exception))

    async def test_update_datastore_raises_exception_on_database_error(self):
        datastore_update = DataStoreUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {}

        self.session_mock.execute.side_effect = SQLAlchemyError('Database error')

        with self.assertRaises(DataStoreUpdateFailed) as context:
            await self.repository.update_datastore(
                datastore_id=self.datastore_id,
                user_id=self.user_id,
                organization_id=self.organization_id,
                datastore_update=datastore_update,
                secrets=secrets
            )

        self.assertIn('Update data store failed', str(context.exception))

    @patch('integration_service.database.repositories.data_store_repository.orm_from_secrets')
    async def test_update_datastore_acquires_advisory_lock(self, orm_from_secrets_mock):
        datastore_update = DataStoreUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {}
        orm_from_secrets_mock.return_value = []

        lock_result_mock = MagicMock()
        version_result_mock = MagicMock()
        version_result_mock.scalar_one.return_value = 0
        update_result_mock = MagicMock()
        update_result_mock.rowcount = 1

        self.session_mock.execute.side_effect = [
            lock_result_mock,
            update_result_mock,
            version_result_mock
        ]

        await self.repository.update_datastore(
            datastore_id=self.datastore_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_update=datastore_update,
            secrets=secrets
        )

        first_call = self.session_mock.execute.await_args_list[0]
        self.assertIsNotNone(first_call)

    @patch('integration_service.database.repositories.data_store_repository.orm_from_secrets')
    async def test_update_datastore_increments_version_correctly(self, orm_from_secrets_mock):
        datastore_update = DataStoreUpdate(
            connection_name='updated-connection',
            port=5433,
            host='updated-host',
            autosync_on=True,
            database_name='updated-database'
        )

        secrets = {
            SecretType.PASSWORD: DataStoreSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                datastore_id=self.datastore_id,
                ciphertext=b'encrypted',
                nonce=b'nonce',
                tag=b'tag',
                wrapped_dek=b'wrapped-dek',
            )
        }

        secrets_orm = [MagicMock()]
        orm_from_secrets_mock.return_value = secrets_orm

        current_version = 10

        lock_result_mock = MagicMock()
        version_result_mock = MagicMock()
        version_result_mock.scalar_one.return_value = current_version
        update_result_mock = MagicMock()
        update_result_mock.rowcount = 1

        self.session_mock.execute.side_effect = [
            lock_result_mock,
            update_result_mock,
            version_result_mock
        ]

        await self.repository.update_datastore(
            datastore_id=self.datastore_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_update=datastore_update,
            secrets=secrets
        )

        orm_from_secrets_mock.assert_called_once_with(secrets, current_version + 1)

    async def test_backend_connector_session_scope_called_correctly(self):
        result_mock = MagicMock()
        result_mock.all.return_value = []
        self.session_mock.execute.return_value = result_mock

        await self.repository.get_user_datastore_ids(
            user_id=self.user_id,
            organization_id=self.organization_id
        )

        self.backend_connector_mock.session_scope.assert_called_once_with(
            self.organization_id,
            self.user_id
        )