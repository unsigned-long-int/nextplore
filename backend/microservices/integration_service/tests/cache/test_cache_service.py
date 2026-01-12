import unittest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from integration_service.cache import CacheService
from integration_service.api.models.filtered_crawl_request import FilteredCrawlRequest
from integration_service.api.models.crawl_response import CrawlResponse
from integration_service.api.models.integration_stats_response import IntegrationStatsResponse
from integration_service.api.models.integration_connection_profile import IntegrationConnectionProfile
from integration_service.api.models.integration_profile import IntegrationProfile
from integration_service.api.models.auth import Auth
from integration_service.api.models.db import DB
from integration_service.api.models.cloud import Cloud
from integration_service.api.models.cert_profile import CertProfile
from integration_service.api.models.cert_state import CertState
from integration_service.api.context import UserIdentity


class TestCacheService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cache_mock = AsyncMock()
        self.cache_service = CacheService(cache=self.cache_mock)

        self.user_identity = UserIdentity(
            user_id=uuid4(),
            organization_id=uuid4()
        )

        self.integration_id = uuid4()

    @patch('integration_service.cache.cache_service.get_cache_key')
    async def test_get_filtered_integration(self, get_cache_key_mock):
        request = FilteredCrawlRequest(
            integrations=[uuid4(), uuid4()],
            schemas={uuid4(): ['schema1', 'schema2']},
            tables={uuid4(): ['table1', 'table2']}
        )

        expected_response = CrawlResponse(
            integration_registry_repr='test-integration',
            integrations_enum=['integration1'],
            schemas_enum=['schema1'],
            tables_enum=['table1'],
            columns_enum=['column1'],
            filter_op_enum=['filter1'],
            agg_funcs_enum=['agg1']
        )

        cache_key = 'filtered-crawl:test-key'
        get_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_filtered_integration(
            user_identity=self.user_identity,
            request=request
        )

        get_cache_key_mock.assert_called_once_with(model=request, prefix='filtered-crawl')
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=CrawlResponse
        )
        self.assertEqual(result, expected_response)

    @patch('integration_service.cache.cache_service.get_cache_key')
    async def test_set_filtered_integration(self, get_cache_key_mock):
        request = FilteredCrawlRequest(
            integrations=[uuid4(), uuid4()],
            schemas={uuid4(): ['schema1', 'schema2']},
            tables={uuid4(): ['table1', 'table2']}
        )

        response = CrawlResponse(
            integration_registry_repr='test-integration',
            integrations_enum=['integration1'],
            schemas_enum=['schema1'],
            tables_enum=['table1'],
            columns_enum=['column1'],
            filter_op_enum=['filter1'],
            agg_funcs_enum=['agg1']
        )

        cache_key = 'filtered-crawl:test-key'
        get_cache_key_mock.return_value = cache_key

        await self.cache_service.set_filtered_integration(
            user_identity=self.user_identity,
            request=request,
            response=response
        )

        get_cache_key_mock.assert_called_once_with(model=request, prefix='filtered-crawl')
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_stats(self, get_string_cache_key_mock):
        expected_response = IntegrationStatsResponse(
            integration_ids=[uuid4(), uuid4()],
            integration_count=2
        )

        cache_key = 'stats:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_stats(
            user_identity=self.user_identity
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='stats'
        )
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=IntegrationStatsResponse
        )
        self.assertEqual(result, expected_response)

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_set_stats(self, get_string_cache_key_mock):
        response = IntegrationStatsResponse(
            integration_ids=[uuid4(), uuid4()],
            integration_count=2
        )

        cache_key = 'stats:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_stats(
            user_identity=self.user_identity,
            response=response
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='stats'
        )
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_connection_profile(self, get_string_cache_key_mock):
        expected_response = IntegrationConnectionProfile(
            id=self.integration_id,
            auth=Auth.IAM,
            cloud=Cloud.AWS,
            db=DB.SQLSERVER,
            connection_name='test-connection',
            database_name='testdb',
            host='localhost',
            port=5432,
            warehouse=None,
            region=None
        )

        cache_key = 'connection-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_connection_profile(
            user_identity=self.user_identity,
            integration_id=self.integration_id
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.integration_id),
            prefix='connection-profile'
        )
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=IntegrationConnectionProfile
        )
        self.assertEqual(result, expected_response)

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_set_connection_profile(self, get_string_cache_key_mock):
        response = IntegrationConnectionProfile(
            id=self.integration_id,
            auth=Auth.IAM,
            cloud=Cloud.AWS,
            db=DB.POSTGRESQL,
            connection_name='test-connection',
            database_name='testdb',
            host='localhost',
            port=5432,
            warehouse=None,
            region=None
        )

        cache_key = 'connection-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_connection_profile(
            user_identity=self.user_identity,
            integration_id=self.integration_id,
            response=response
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.integration_id),
            prefix='connection-profile'
        )
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_profiles(self, get_string_cache_key_mock):
        expected_response = [
            IntegrationProfile(
                id=uuid4(),
                auth=Auth.IAM,
                cloud=Cloud.GCP,
                db=DB.POSTGRESQL,
                connection_name='connection1',
                database_name='db1',
                host='localhost',
                port=5432,
                autosync_on=True
            ),
            IntegrationProfile(
                id=uuid4(),
                auth=Auth.PASSWORD_NATIVE,
                cloud=Cloud.AZURE,
                db=DB.MYSQL,
                connection_name='connection2',
                database_name='db2',
                host='localhost',
                port=3306,
                autosync_on=False
            )
        ]

        cache_key = 'profile:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = expected_response

        result = await self.cache_service.get_profiles(
            user_identity=self.user_identity
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='profile'
        )
        self.cache_mock.get_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=IntegrationProfile
        )
        self.assertEqual(result, expected_response)

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_set_profiles(self, get_string_cache_key_mock):
        response = [
            IntegrationProfile(
                id=uuid4(),
                auth=Auth.PASSWORD_PROXY,
                cloud=Cloud.GCP,
                db=DB.POSTGRESQL,
                connection_name='connection1',
                database_name='db1',
                host='localhost',
                port=5432,
                autosync_on=True
            )
        ]

        cache_key = 'profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_profiles(
            user_identity=self.user_identity,
            response=response
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='profile'
        )
        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_cert_profiles(self, get_string_cache_key_mock):
        now = datetime.utcnow()
        expected_response = [
            CertProfile(
                id=uuid4(),
                state=CertState.PENDING,
                cert_kid='cert_kid',
                cert_name='cert1',
                public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
                thumbprint_sha256='thumbprint1',
                not_before=now,
                not_after=now,
                created_at=now,
                assigned_at=now,
                activated_at=now
            ),
            CertProfile(
                id=uuid4(),
                state=CertState.PENDING,
                cert_kid='cert-kid',
                cert_name='cert2',
                public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
                thumbprint_sha256='thumbprint1',
                not_before=now,
                not_after=now,
                created_at=now,
                assigned_at=now,
                activated_at=now
            )
        ]

        cache_key = 'cert-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = expected_response

        result = await self.cache_service.get_cert_profiles(
            user_identity=self.user_identity
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='cert-profile'
        )
        self.cache_mock.get_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=CertProfile
        )
        self.assertEqual(result, expected_response)

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_set_cert_profiles(self, get_string_cache_key_mock):
        now = datetime.utcnow()
        response = [
            CertProfile(
                id=uuid4(),
                state=CertState.PENDING,
                cert_kid='cert-kid-active',
                cert_name='active-cert',
                public_cert_pem='-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
                thumbprint_sha256='thumbprint1',
                not_before=now,
                not_after=now,
                created_at=now,
                assigned_at=now,
                activated_at=now
            )
        ]

        cache_key = 'cert-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_cert_profiles(
            user_identity=self.user_identity,
            response=response
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='cert-profile'
        )
        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_delete_cert_profiles(self, get_string_cache_key_mock):
        cache_key = 'cert-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.delete_cert_profiles(
            user_identity=self.user_identity
        )

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='cert-profile'
        )
        self.cache_mock.delete.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_profiles_returns_empty_list(self, get_string_cache_key_mock):
        cache_key = 'profile:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = []

        result = await self.cache_service.get_profiles(
            user_identity=self.user_identity
        )

        self.assertEqual(result, [])
        self.cache_mock.get_many.assert_awaited_once()

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_cert_profiles_returns_empty_list(self, get_string_cache_key_mock):
        cache_key = 'cert-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = []

        result = await self.cache_service.get_cert_profiles(
            user_identity=self.user_identity
        )

        self.assertEqual(result, [])
        self.cache_mock.get_many.assert_awaited_once()

    @patch('integration_service.cache.cache_service.get_cache_key')
    async def test_get_filtered_integration_returns_none(self, get_cache_key_mock):
        request = FilteredCrawlRequest(
            integrations=[uuid4()],
            schemas={},
            tables={}
        )

        cache_key = 'filtered-crawl:test-key'
        get_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = None

        result = await self.cache_service.get_filtered_integration(
            user_identity=self.user_identity,
            request=request
        )

        self.assertIsNone(result)
        self.cache_mock.get_one.assert_awaited_once()

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_get_connection_profile_returns_none(self, get_string_cache_key_mock):
        cache_key = 'connection-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = None

        result = await self.cache_service.get_connection_profile(
            user_identity=self.user_identity,
            integration_id=self.integration_id
        )

        self.assertIsNone(result)
        self.cache_mock.get_one.assert_awaited_once()

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_cache_key_generation_uses_user_and_org_id(self, get_string_cache_key_mock):
        cache_key = 'stats:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.get_stats(user_identity=self.user_identity)

        expected_value = f'{str(self.user_identity.user_id)}{str(self.user_identity.organization_id)}'
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value,
            prefix='stats'
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_connection_profile_cache_key_uses_integration_id(self, get_string_cache_key_mock):
        cache_key = 'connection-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.get_connection_profile(
            user_identity=self.user_identity,
            integration_id=self.integration_id
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.integration_id),
            prefix='connection-profile'
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_set_profiles_with_empty_list(self, get_string_cache_key_mock):
        cache_key = 'profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_profiles(
            user_identity=self.user_identity,
            response=[]
        )

        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=[]
        )

    @patch('integration_service.cache.cache_service.get_string_cache_key')
    async def test_set_cert_profiles_with_empty_list(self, get_string_cache_key_mock):
        cache_key = 'cert-profile:test-key'
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_cert_profiles(
            user_identity=self.user_identity,
            response=[]
        )

        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=[]
        )
