import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import OperationalError
from svc_integration_contracts.models import Auth, DB, Cloud

from integration_service.services.crawl.catalog_builder import (
    build_integrations_registry_catalog
)
from integration_service.services.crawl.catalogs import (
    IntegrationRegistryCatalog,
    SchemaCatalog
)
from integration_service.services.crawl.exceptions import CrawlIntegrationsFailed
from integration_service.domain.models.integration import Integration
from integration_service.domain.models.secret import IntegrationSecret, SecretType
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile
from nextplore_sdk.database.connection_maker.exc.exceptions import ConnectionFailed
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager


class TestBuildIntegrationsRegistryCatalog(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.backend_connector = MagicMock(spec=DatabaseBackendConnector)
        self.engine_manager = MagicMock(spec=EngineManager)
        self.engine_manager.acquire_engine = AsyncMock()

        self.user_id = uuid4()
        self.organization_id = uuid4()
        self.integration_id_1 = uuid4()
        self.integration_id_2 = uuid4()
        self.kek_kid = 'kek_kid'

        self.mock_integration = Integration(
            id=self.integration_id_1,
            organization_id=self.organization_id,
            user_id=self.user_id,
            auth=Auth.iam,
            cloud=Cloud.azure,
            db=DB.sqlserver,
            connection_name='test_integration',
            host='test.com',
            database_name='test_db',
            kek_kid=self.kek_kid,
            port=443,
            warehouse='test_warehouse',
            tenant_id='tenant_id',
            client_id='client_id',
            region='us-east-1',
            azure_cert_kid='cert_123',
            azure_cert_name='test_cert',
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True
        )

        self.mock_secrets = {
            SecretType.USERNAME: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id_1,
                ciphertext=b'encrypted_username',
                nonce=b'nonce_1',
                tag=b'tag_1',
                wrapped_dek=b'wrapped_key_1',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
                version=1
            ),
            SecretType.PASSWORD: IntegrationSecret(
                organization_id=self.organization_id,
                user_id=self.user_id,
                integration_id=self.integration_id_1,
                ciphertext=b'encrypted_password',
                nonce=b'nonce_2',
                tag=b'tag_2',
                wrapped_dek=b'wrapped_key_2',
                enc_alg='AES-256-GCM',
                wrap_alg='RSA-OAEP',
                encoding='base64',
                version=1
            )
        }

        self.mock_schemas = [
            SchemaCatalog(
                integration_id=self.integration_id_1,
                name='schema1',
                tables=[]
            ),
            SchemaCatalog(
                integration_id=self.integration_id_1,
                name='schema2',
                tables=[]
            )
        ]

        self.mock_integration_spec = MagicMock()
        self.mock_integration_spec.is_satisfied_by = MagicMock(return_value=True)

        self.mock_schema_spec = MagicMock()
        self.mock_table_spec = MagicMock()

        self.mock_engine = MagicMock()

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_successful_crawl_single_integration(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(return_value=self.mock_integration)
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client = MagicMock()
        mock_crypto_client_cls.return_value = mock_crypto_client

        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: f'decrypted_{secret_type}'
        mock_build_schemas.return_value = self.mock_schemas

        self.engine_manager.acquire_engine.return_value = self.mock_engine

        result = await build_integrations_registry_catalog(
            backend_connector=self.backend_connector,
            engine_manager=self.engine_manager,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_ids=[self.integration_id_1],
            integration_spec=self.mock_integration_spec,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertIsInstance(result, IntegrationRegistryCatalog)
        self.assertEqual(len(result.integrations), 1)
        self.assertEqual(result.integrations[0].id, self.integration_id_1)
        self.assertEqual(len(result.integrations[0].schemas), 2)

        mock_repo.get_integration_by_id.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_id=self.integration_id_1
        )
        mock_repo.get_secrets.assert_called_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            integration_id=self.integration_id_1
        )

        mock_crypto_client_cls.assert_called_once_with(self.kek_kid)

        self.engine_manager.acquire_engine.assert_called_once()

        mock_build_schemas.assert_called_once()

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_successful_crawl_multiple_integrations(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        integration_2 = Integration(
            id=self.integration_id_2,
            organization_id=self.organization_id,
            user_id=self.user_id,
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name='test_integration_2',
            host='db.example.com',
            database_name='test_db_2',
            kek_kid=self.kek_kid,
            port=5432,
            warehouse=None,
            tenant_id=None,
            client_id=None,
            region='us-west-2',
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True
        )

        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(
            side_effect=[self.mock_integration, integration_2]
        )
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()
        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: f'decrypted_{secret_type}'
        mock_build_schemas.return_value = self.mock_schemas

        self.engine_manager.acquire_engine.return_value = self.mock_engine

        result = await build_integrations_registry_catalog(
            backend_connector=self.backend_connector,
            engine_manager=self.engine_manager,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_ids=[self.integration_id_1, self.integration_id_2],
            integration_spec=self.mock_integration_spec,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result.integrations), 2)
        self.assertEqual(mock_repo.get_integration_by_id.call_count, 2)
        self.assertEqual(mock_build_schemas.call_count, 2)

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_skips_integration_not_satisfying_spec(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        self.mock_integration_spec.is_satisfied_by.return_value = False

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        with self.assertRaises(CrawlIntegrationsFailed) as context:
            await build_integrations_registry_catalog(
                backend_connector=self.backend_connector,
                engine_manager=self.engine_manager,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_ids=[self.integration_id_1],
                integration_spec=self.mock_integration_spec,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec
            )

        self.assertIn('None of the 1 integrations', str(context.exception))

        mock_repo.get_integration_by_id.assert_not_called()

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_handles_connection_failed_gracefully(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(return_value=self.mock_integration)
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()
        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: f'decrypted_{secret_type}'

        self.engine_manager.acquire_engine.side_effect = ConnectionFailed('Connection refused')

        with self.assertRaises(CrawlIntegrationsFailed) as context:
            await build_integrations_registry_catalog(
                backend_connector=self.backend_connector,
                engine_manager=self.engine_manager,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_ids=[self.integration_id_1],
                integration_spec=self.mock_integration_spec,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec
            )

        self.assertEqual(context.exception.failed_ids, [self.integration_id_1])

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_handles_operational_error_gracefully(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(return_value=self.mock_integration)
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()
        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: f'decrypted_{secret_type}'

        self.engine_manager.acquire_engine.return_value = self.mock_engine

        mock_build_schemas.side_effect = OperationalError('SELECT 1', {}, Exception('DB error'))

        with self.assertRaises(CrawlIntegrationsFailed):
            await build_integrations_registry_catalog(
                backend_connector=self.backend_connector,
                engine_manager=self.engine_manager,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_ids=[self.integration_id_1],
                integration_spec=self.mock_integration_spec,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec
            )

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_handles_unexpected_exception_gracefully(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(return_value=self.mock_integration)
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()
        mock_decrypt_secret.side_effect = Exception('Unexpected decryption error')

        with self.assertRaises(CrawlIntegrationsFailed):
            await build_integrations_registry_catalog(
                backend_connector=self.backend_connector,
                engine_manager=self.engine_manager,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_ids=[self.integration_id_1],
                integration_spec=self.mock_integration_spec,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec
            )

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_partial_success_with_multiple_integrations(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        integration_2 = Integration(
            id=self.integration_id_2,
            organization_id=self.organization_id,
            user_id=self.user_id,
            auth=Auth.secret,
            cloud=Cloud.gcp,
            db=DB.mysql,
            connection_name='test_integration_2',
            host='db.example.com',
            database_name='test_db_2',
            kek_kid=self.kek_kid,
            port=5432,
            warehouse=None,
            tenant_id=None,
            client_id=None,
            region='us-west-2',
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=True
        )

        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(
            side_effect=[self.mock_integration, integration_2]
        )
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()
        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: f'decrypted_{secret_type}'

        self.engine_manager.acquire_engine.side_effect = [
            self.mock_engine,
            ConnectionFailed('Connection refused')
        ]
        mock_build_schemas.return_value = self.mock_schemas

        result = await build_integrations_registry_catalog(
            backend_connector=self.backend_connector,
            engine_manager=self.engine_manager,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_ids=[self.integration_id_1, self.integration_id_2],
            integration_spec=self.mock_integration_spec,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.assertEqual(len(result.integrations), 1)
        self.assertEqual(result.integrations[0].id, self.integration_id_1)

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_skips_integration_with_no_schemas(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(return_value=self.mock_integration)
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()
        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: f'decrypted_{secret_type}'

        self.engine_manager.acquire_engine.return_value = self.mock_engine

        mock_build_schemas.return_value = []

        with self.assertRaises(CrawlIntegrationsFailed):
            await build_integrations_registry_catalog(
                backend_connector=self.backend_connector,
                engine_manager=self.engine_manager,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_ids=[self.integration_id_1],
                integration_spec=self.mock_integration_spec,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec
            )

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_connection_profile_constructed_correctly(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(return_value=self.mock_integration)
        mock_repo.get_secrets = AsyncMock(return_value=self.mock_secrets)
        mock_repo_cls.return_value = mock_repo

        mock_crypto_client_cls.return_value = MagicMock()

        decrypted_values = {
            SecretType.USERNAME: 'test_user',
            SecretType.PASSWORD: 'test_password',
            SecretType.CLIENT_SECRET: 'test_secret',
            SecretType.AWS_EXTERNAL_ID: None,
            SecretType.AWS_ROLE_ARN: None,
            SecretType.SNOWFLAKE_PRIVATE_KEY: 'test_private_key'
        }
        mock_decrypt_secret.side_effect = lambda secret_type, secrets, client: decrypted_values.get(secret_type)

        mock_build_schemas.return_value = self.mock_schemas
        self.engine_manager.acquire_engine.return_value = self.mock_engine

        await build_integrations_registry_catalog(
            backend_connector=self.backend_connector,
            engine_manager=self.engine_manager,
            user_id=self.user_id,
            organization_id=self.organization_id,
            integration_ids=[self.integration_id_1],
            integration_spec=self.mock_integration_spec,
            schema_spec=self.mock_schema_spec,
            table_spec=self.mock_table_spec
        )

        self.engine_manager.acquire_engine.assert_called_once()
        connection_profile = self.engine_manager.acquire_engine.call_args[0][0]

        self.assertIsInstance(connection_profile, ConnectionProfile)
        self.assertEqual(connection_profile.database, 'test_db')
        self.assertEqual(connection_profile.port, 443)
        self.assertEqual(connection_profile.host, 'test.com')
        self.assertEqual(connection_profile.warehouse, 'test_warehouse')
        self.assertEqual(connection_profile.username, 'test_user')
        self.assertEqual(connection_profile.password, 'test_password')
        self.assertEqual(connection_profile.client_secret, 'test_secret')
        self.assertEqual(connection_profile.snowflake_private_key, 'test_private_key')

    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.build_schemas_catalog')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.decrypt_secret')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.AzureCryptoClient')
    @patch('integration_service.services.crawl.catalog_builder.build_integrations_registry_catalog.IntegrationRepository')
    async def test_raises_crawl_failed_when_all_integrations_fail(
            self,
            mock_repo_cls,
            mock_crypto_client_cls,
            mock_decrypt_secret,
            mock_build_schemas
    ):
        mock_repo = MagicMock()
        mock_repo.get_integration_by_id = AsyncMock(side_effect=Exception('DB error'))
        mock_repo_cls.return_value = mock_repo

        integration_ids = [self.integration_id_1, self.integration_id_2]

        with self.assertRaises(CrawlIntegrationsFailed) as context:
            await build_integrations_registry_catalog(
                backend_connector=self.backend_connector,
                engine_manager=self.engine_manager,
                user_id=self.user_id,
                organization_id=self.organization_id,
                integration_ids=integration_ids,
                integration_spec=self.mock_integration_spec,
                schema_spec=self.mock_schema_spec,
                table_spec=self.mock_table_spec
            )

        self.assertIn('None of the 2 integrations', str(context.exception))
        self.assertEqual(context.exception.failed_ids, integration_ids)
