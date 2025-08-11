import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy.exc import OperationalError

from services.integration_registry_crawl_service import (
    crawl_integration_registry,
    CrawlIntegrationsFailed,
)
import services.integration_registry_crawl_service as mod


class TestCrawlIntegrationRegistry(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.connector = object()
        self.user_id = uuid4()
        self.org_id = uuid4()

        self.integration_spec = Mock()
        self.schema_spec = Mock()
        self.table_spec = Mock()

    @patch('services.integration_registry_crawl_service.IntegrationRegistryCatalog')
    @patch('services.integration_registry_crawl_service.IntegrationCatalog')
    @patch('services.integration_registry_crawl_service.crawl_schemas')
    @patch('services.integration_registry_crawl_service.get_crawler')
    @patch('services.integration_registry_crawl_service.build_connection_string')
    @patch('services.integration_registry_crawl_service.ConnectionMeta')
    @patch('services.integration_registry_crawl_service.decrypt_integration')
    @patch('services.integration_registry_crawl_service.IntegrationRepository')
    async def test_success_with_filtering_and_schemas(
        self,
        mock_repo_cls,
        mock_decrypt,
        mock_conn_meta,
        mock_build_conn_str,
        mock_get_crawler,
        mock_crawl_schemas,
        mock_integration_catalog_cls,
        mock_registry_catalog_cls,
    ):
        ids = [uuid4(), uuid4(), uuid4()]

        repo = Mock()
        repo.get_integration_by_id = AsyncMock(return_value='encrypted')
        mock_repo_cls.return_value = repo

        decrypted = SimpleNamespace(
            service_type='postgres',
            auth_method='password',
            host='db.local', port=5432,
            database_name='analytics',
            username='alice', password='secret',
            kerberos_principal=None, windows_domain=None,
            extra_options={'sslmode': 'require'},
        )
        mock_decrypt.return_value = decrypted

        mock_conn_meta.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)

        mock_build_conn_str.return_value = 'conn://string'
        mock_get_crawler.return_value = 'crawler'

        mock_crawl_schemas.side_effect = [
            ['schema_1'],
            [],
        ]

        mock_integration_catalog_cls.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
        mock_registry_catalog_cls.side_effect = lambda **kwargs: kwargs

        self.integration_spec.is_satisfied_by.side_effect = [True, False, True]

        out = await crawl_integration_registry(
            connector=self.connector,
            user_id=self.user_id,
            organization_id=self.org_id,
            integration_ids=ids,
            integration_spec=self.integration_spec,
            schema_spec=self.schema_spec,
            table_spec=self.table_spec,
        )

        self.assertIn('integrations', out)
        integrations = out['integrations']
        self.assertEqual(len(integrations), 1)
        self.assertEqual(integrations[0].id, ids[0])

        self.assertEqual(repo.get_integration_by_id.await_count, 2)

    @patch('services.integration_registry_crawl_service.IntegrationRegistryCatalog')
    @patch('services.integration_registry_crawl_service.IntegrationCatalog')
    @patch('services.integration_registry_crawl_service.crawl_schemas')
    @patch('services.integration_registry_crawl_service.get_crawler')
    @patch('services.integration_registry_crawl_service.build_connection_string')
    @patch('services.integration_registry_crawl_service.ConnectionMeta')
    @patch('services.integration_registry_crawl_service.decrypt_integration')
    @patch('services.integration_registry_crawl_service.IntegrationRepository')
    async def test_all_filtered_or_empty_raises(
        self,
        mock_repo_cls,
        mock_decrypt,
        mock_conn_meta,
        mock_build_conn_str,
        mock_get_crawler,
        mock_crawl_schemas,
        mock_integration_catalog_cls,
        mock_registry_catalog_cls,
    ):
        ids = [uuid4(), uuid4()]

        repo = Mock()
        repo.get_integration_by_id = AsyncMock(return_value='encrypted')
        mock_repo_cls.return_value = repo
        decrypted = SimpleNamespace(
            service_type='postgres', auth_method='password',
            host='h', port=5432, database_name='db',
            username='u', password='p',
            kerberos_principal=None, windows_domain=None, extra_options=None,
        )
        mock_decrypt.return_value = decrypted
        mock_conn_meta.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_build_conn_str.return_value = 'conn://'
        mock_get_crawler.return_value = 'crawler'

        mock_crawl_schemas.side_effect = [[], []]
        mock_integration_catalog_cls.side_effect = lambda **kw: SimpleNamespace(**kw)

        self.integration_spec.is_satisfied_by.side_effect = [True, True]

        with self.assertRaises(CrawlIntegrationsFailed) as ctx:
            await crawl_integration_registry(
                connector=self.connector,
                user_id=self.user_id,
                organization_id=self.org_id,
                integration_ids=ids,
                integration_spec=self.integration_spec,
                schema_spec=self.schema_spec,
                table_spec=self.table_spec,
            )

        err = ctx.exception
        self.assertEqual(err.failed_ids, ids)
        self.assertIn(str(len(ids)), err.message)

    @patch('services.integration_registry_crawl_service.IntegrationRegistryCatalog')
    @patch('services.integration_registry_crawl_service.IntegrationCatalog')
    @patch('services.integration_registry_crawl_service.crawl_schemas')
    @patch('services.integration_registry_crawl_service.get_crawler')
    @patch('services.integration_registry_crawl_service.build_connection_string')
    @patch('services.integration_registry_crawl_service.ConnectionMeta')
    @patch('services.integration_registry_crawl_service.decrypt_integration')
    @patch('services.integration_registry_crawl_service.IntegrationRepository')
    async def test_handles_connection_operational_and_generic_errors_and_still_returns_success(
        self,
        mock_repo_cls,
        mock_decrypt,
        mock_conn_meta,
        mock_build_conn_str,
        mock_get_crawler,
        mock_crawl_schemas,
        mock_integration_catalog_cls,
        mock_registry_catalog_cls,
    ):
        from nextplore_shared.database.sql_connection_service.session_starter import ConnectionFailed
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        ids = [a, b, c, d]

        repo = Mock()
        repo.get_integration_by_id = AsyncMock(return_value='encrypted')
        mock_repo_cls.return_value = repo

        def decrypt_side_effect(_enc):
            if decrypt_side_effect.counter == 2:
                decrypt_side_effect.counter += 1
                raise RuntimeError('boom')
            decrypt_side_effect.counter += 1
            return SimpleNamespace(
                service_type='postgres', auth_method='password',
                host='h', port=5432, database_name='db',
                username='u', password='p',
                kerberos_principal=None, windows_domain=None, extra_options=None,
            )
        decrypt_side_effect.counter = 0
        mock_decrypt.side_effect = decrypt_side_effect

        mock_conn_meta.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_build_conn_str.return_value = 'conn://'

        def crawler_side_effect(_cs):
            if crawler_side_effect.counter == 0:
                crawler_side_effect.counter += 1
                raise ConnectionFailed('conn fail')
            crawler_side_effect.counter += 1
            return 'crawler'
        crawler_side_effect.counter = 0
        mock_get_crawler.side_effect = crawler_side_effect

        def crawl_side_effect(crawler, integration_id, schema_spec, table_spec):
            if crawl_side_effect.counter == 0:
                crawl_side_effect.counter += 1
                raise OperationalError('select 1', {}, 'opfail')
            crawl_side_effect.counter += 1
            if integration_id == d:
                return ['s']
            return []
        crawl_side_effect.counter = 0
        mock_crawl_schemas.side_effect = crawl_side_effect

        mock_integration_catalog_cls.side_effect = lambda **kw: SimpleNamespace(**kw)
        mock_registry_catalog_cls.side_effect = lambda **kw: kw

        self.integration_spec.is_satisfied_by.side_effect = [True, True, True, True]

        out = await crawl_integration_registry(
            connector=self.connector,
            user_id=self.user_id,
            organization_id=self.org_id,
            integration_ids=ids,
            integration_spec=self.integration_spec,
            schema_spec=self.schema_spec,
            table_spec=self.table_spec,
        )

        self.assertIn('integrations', out)
        integrations = out['integrations']
        self.assertEqual(len(integrations), 1)
        self.assertEqual(integrations[0].id, d)
