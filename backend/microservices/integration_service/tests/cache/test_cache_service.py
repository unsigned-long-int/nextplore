import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from svc_integration_contracts.models import (
    DB,
    Auth,
    CertProfile,
    CertState,
    Cloud,
    CrawlResponse,
    DataStoreConnectionProfile,
    DataStoreProfile,
    DataStoreStatsResponse,
    FilteredCrawlRequest,
    UserLlmConfig,
    UserLlmProfile,
)

from integration_service.api.context import UserIdentity
from integration_service.cache import CacheService


class TestCacheService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cache_mock = AsyncMock()
        self.cache_service = CacheService(cache=self.cache_mock)

        self.user_identity = UserIdentity(user_id=uuid4(), organization_id=uuid4())

        self.datastore_id = uuid4()
        self.model_ref_id = uuid4()

    @patch("integration_service.cache.cache_service.get_cache_key")
    async def test_get_filtered_datastore(self, get_cache_key_mock):
        request = FilteredCrawlRequest(
            datastores=[uuid4(), uuid4()],
            schemas={str(uuid4()): ["schema1", "schema2"]},
            tables={str(uuid4()): ["table1", "table2"]},
        )
        expected_response = CrawlResponse(
            datastore_registry_repr="test-data_store",
            datastores_enum=["datastore1"],
            schemas_enum=["schema1"],
            tables_enum=["table1"],
            columns_enum=["column1"],
            filter_op_enum=["filter1"],
            agg_funcs_enum=["agg1"],
        )
        cache_key = "datastore-filtered-crawl:test-key"
        get_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_filtered_datastore(
            user_identity=self.user_identity, request=request
        )

        get_cache_key_mock.assert_called_once_with(
            model=request, prefix="datastore-filtered-crawl"
        )
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=CrawlResponse,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_cache_key")
    async def test_set_filtered_datastore(self, get_cache_key_mock):
        request = FilteredCrawlRequest(
            datastores=[uuid4(), uuid4()],
            schemas={str(uuid4()): ["schema1", "schema2"]},
            tables={str(uuid4()): ["table1", "table2"]},
        )
        response = CrawlResponse(
            datastore_registry_repr="test-data_store",
            datastores_enum=["datastore1"],
            schemas_enum=["schema1"],
            tables_enum=["table1"],
            columns_enum=["column1"],
            filter_op_enum=["filter1"],
            agg_funcs_enum=["agg1"],
        )
        cache_key = "datastore-filtered-crawl:test-key"
        get_cache_key_mock.return_value = cache_key

        await self.cache_service.set_filtered_datastore(
            user_identity=self.user_identity, request=request, response=response
        )

        get_cache_key_mock.assert_called_once_with(
            model=request, prefix="datastore-filtered-crawl"
        )
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_cache_key")
    async def test_get_filtered_datastore_returns_none(self, get_cache_key_mock):
        request = FilteredCrawlRequest(datastores=[uuid4()], schemas={}, tables={})
        get_cache_key_mock.return_value = "filtered-crawl:test-key"
        self.cache_mock.get_one.return_value = None

        result = await self.cache_service.get_filtered_datastore(
            user_identity=self.user_identity, request=request
        )

        self.assertIsNone(result)
        self.cache_mock.get_one.assert_awaited_once()

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_datastore_stats(self, get_string_cache_key_mock):
        expected_response = DataStoreStatsResponse(
            datastore_ids=[uuid4(), uuid4()], datastore_count=2
        )
        cache_key = "datastore-stats:test-key"
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_datastore_stats(
            user_identity=self.user_identity
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-stats"
        )
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=DataStoreStatsResponse,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_datastore_stats(self, get_string_cache_key_mock):
        response = DataStoreStatsResponse(datastore_ids=[uuid4()], datastore_count=1)
        cache_key = "datastore-stats:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_datastore_stats(
            user_identity=self.user_identity, response=response
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-stats"
        )
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_datastore_connection_profile(self, get_string_cache_key_mock):
        expected_response = DataStoreConnectionProfile(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.sqlserver,
            database_name="testdb",
            host="localhost",
            port=5432,
            warehouse=None,
            region=None,
        )
        cache_key = "datastore-connection-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_datastore_connection_profile(
            user_identity=self.user_identity, datastore_id=self.datastore_id
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.datastore_id), prefix="datastore-connection-profile"
        )
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=DataStoreConnectionProfile,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_datastore_connection_profile(self, get_string_cache_key_mock):
        response = DataStoreConnectionProfile(
            auth=Auth.iam,
            cloud=Cloud.aws,
            db=DB.postgresql,
            database_name="testdb",
            host="localhost",
            port=5432,
            warehouse=None,
            region=None,
        )
        cache_key = "datastore-connection-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_datastore_connection_profile(
            user_identity=self.user_identity,
            datastore_id=self.datastore_id,
            response=response,
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.datastore_id), prefix="datastore-connection-profile"
        )
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_connection_profile_returns_none(self, get_string_cache_key_mock):
        get_string_cache_key_mock.return_value = "connection-profile:test-key"
        self.cache_mock.get_one.return_value = None

        result = await self.cache_service.get_datastore_connection_profile(
            user_identity=self.user_identity, datastore_id=self.datastore_id
        )

        self.assertIsNone(result)
        self.cache_mock.get_one.assert_awaited_once()

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_datastore_profiles(self, get_string_cache_key_mock):
        expected_response = [
            DataStoreProfile(
                id=uuid4(),
                auth=Auth.iam,
                cloud=Cloud.gcp,
                db=DB.postgresql,
                connection_name="connection1",
                database_name="db1",
                host="localhost",
                port=5432,
                autosync_on=True,
            ),
            DataStoreProfile(
                id=uuid4(),
                auth=Auth.password_native,
                cloud=Cloud.azure,
                db=DB.mysql,
                connection_name="connection2",
                database_name="db2",
                host="localhost",
                port=3306,
                autosync_on=False,
            ),
        ]
        cache_key = "datastore-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = expected_response

        result = await self.cache_service.get_datastore_profiles(
            user_identity=self.user_identity
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-profile"
        )
        self.cache_mock.get_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=DataStoreProfile,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_datastore_profiles(self, get_string_cache_key_mock):
        response = [
            DataStoreProfile(
                id=uuid4(),
                auth=Auth.password_native,
                cloud=Cloud.gcp,
                db=DB.postgresql,
                connection_name="connection1",
                database_name="db1",
                host="localhost",
                port=5432,
                autosync_on=True,
            )
        ]
        cache_key = "datastore-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_datastore_profiles(
            user_identity=self.user_identity, response=response
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-profile"
        )
        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_datastore_profiles_returns_empty_list(
        self, get_string_cache_key_mock
    ):
        get_string_cache_key_mock.return_value = "datastore-profile:test-key"
        self.cache_mock.get_many.return_value = []

        result = await self.cache_service.get_datastore_profiles(
            user_identity=self.user_identity
        )

        self.assertEqual(result, [])
        self.cache_mock.get_many.assert_awaited_once()

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_datastore_profiles_with_empty_list(
        self, get_string_cache_key_mock
    ):
        get_string_cache_key_mock.return_value = "datastore-profile:test-key"

        await self.cache_service.set_datastore_profiles(
            user_identity=self.user_identity, response=[]
        )

        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            "datastore-profile:test-key",
            value=[],
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_cert_profiles(self, get_string_cache_key_mock):
        now = datetime.now(timezone.utc)
        expected_response = [
            CertProfile(
                id=uuid4(),
                state=CertState.pending,
                cert_kid="cert_kid_1",
                cert_name="cert1",
                public_cert_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                thumbprint_sha256="thumbprint1",
                not_before=now,
                not_after=now,
                created_at=now,
                assigned_at=now,
                activated_at=now,
            ),
        ]
        cache_key = "datastore-cert-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = expected_response

        result = await self.cache_service.get_datastore_cert_profiles(
            user_identity=self.user_identity
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-cert-profile"
        )
        self.cache_mock.get_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=CertProfile,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_cert_profiles(self, get_string_cache_key_mock):
        now = datetime.now(timezone.utc)
        response = [
            CertProfile(
                id=uuid4(),
                state=CertState.pending,
                cert_kid="cert-kid-active",
                cert_name="active-cert",
                public_cert_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                thumbprint_sha256="thumbprint1",
                not_before=now,
                not_after=now,
                created_at=now,
                assigned_at=now,
                activated_at=now,
            )
        ]
        cache_key = "datastore-cert-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_datastore_cert_profiles(
            user_identity=self.user_identity, response=response
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-cert-profile"
        )
        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_delete_cert_profiles(self, get_string_cache_key_mock):
        cache_key = "datastore-cert-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.delete_datastore_cert_profiles(
            user_identity=self.user_identity
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="datastore-cert-profile"
        )
        self.cache_mock.delete.assert_awaited_once_with(
            self.user_identity.organization_id, self.user_identity.user_id, cache_key
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_cert_profiles_returns_empty_list(
        self, get_string_cache_key_mock
    ):
        get_string_cache_key_mock.return_value = "datastore-cert-profile:test-key"
        self.cache_mock.get_many.return_value = []

        result = await self.cache_service.get_datastore_cert_profiles(
            user_identity=self.user_identity
        )

        self.assertEqual(result, [])
        self.cache_mock.get_many.assert_awaited_once()

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_cert_profiles_with_empty_list(self, get_string_cache_key_mock):
        get_string_cache_key_mock.return_value = "datastore-cert-profile:test-key"

        await self.cache_service.set_datastore_cert_profiles(
            user_identity=self.user_identity, response=[]
        )

        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            "datastore-cert-profile:test-key",
            value=[],
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_user_llm_profiles(self, get_string_cache_key_mock):
        expected_response = [
            UserLlmProfile(
                model_id="gpt-4o",
                label="GPT-4o",
                api_base="https://api.openai.org",
                max_tokens=10,
                model_ref_id=uuid4(),
            ),
            UserLlmProfile(
                model_id="anthropuc",
                label="opus",
                api_base="https://api.anthropic.org",
                max_tokens=10,
                model_ref_id=uuid4(),
            ),
        ]
        cache_key = "user-llm-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_many.return_value = expected_response

        result = await self.cache_service.get_user_llm_profiles(
            user_identity=self.user_identity
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="user-llm-profile"
        )
        self.cache_mock.get_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=UserLlmProfile,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_user_llm_profiles(self, get_string_cache_key_mock):
        response = [
            UserLlmProfile(
                model_id="gpt-4o",
                label="GPT-4o",
                api_base="https://api.openai.org",
                max_tokens=10,
                model_ref_id=uuid4(),
            ),
        ]
        cache_key = "user-llm-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_user_llm_profiles(
            user_identity=self.user_identity, response=response
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="user-llm-profile"
        )
        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_delete_user_llm_profiles(self, get_string_cache_key_mock):
        cache_key = "user-llm-profile:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.delete_user_llm_profiles(
            user_identity=self.user_identity
        )

        expected_value = f"{self.user_identity.user_id!s}{self.user_identity.organization_id!s}"
        get_string_cache_key_mock.assert_called_once_with(
            value=expected_value, prefix="user-llm-profile"
        )
        self.cache_mock.delete.assert_awaited_once_with(
            self.user_identity.organization_id, self.user_identity.user_id, cache_key
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_user_llm_profiles_returns_empty_list(
        self, get_string_cache_key_mock
    ):
        get_string_cache_key_mock.return_value = "user-llm-profile:test-key"
        self.cache_mock.get_many.return_value = []

        result = await self.cache_service.get_user_llm_profiles(
            user_identity=self.user_identity
        )

        self.assertEqual(result, [])
        self.cache_mock.get_many.assert_awaited_once()

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_user_llm_profiles_with_empty_list(
        self, get_string_cache_key_mock
    ):
        get_string_cache_key_mock.return_value = "user-llm-profile:test-key"

        await self.cache_service.set_user_llm_profiles(
            user_identity=self.user_identity, response=[]
        )

        self.cache_mock.set_many.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            "user-llm-profile:test-key",
            value=[],
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_user_llm_config(self, get_string_cache_key_mock):
        expected_response = UserLlmConfig(
            api_base="test-api-base",
            connection_params={"api_key": "test-api-key"},
            max_tokens=4256,
        )
        cache_key = "user-llm-config:test-key"
        get_string_cache_key_mock.return_value = cache_key
        self.cache_mock.get_one.return_value = expected_response

        result = await self.cache_service.get_user_llm_config(
            user_identity=self.user_identity, model_ref_id=self.model_ref_id
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.model_ref_id), prefix="user-llm-config"
        )
        self.cache_mock.get_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            model=UserLlmConfig,
        )
        self.assertEqual(result, expected_response)

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_set_user_llm_config(self, get_string_cache_key_mock):
        response = UserLlmConfig(
            api_base="test-api-base",
            connection_params={"api_key": "test-api-key"},
            max_tokens=4256,
        )
        cache_key = "user-llm-config:test-key"
        get_string_cache_key_mock.return_value = cache_key

        await self.cache_service.set_user_llm_config(
            user_identity=self.user_identity,
            model_ref_id=self.model_ref_id,
            response=response,
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.model_ref_id), prefix="user-llm-config"
        )
        self.cache_mock.set_one.assert_awaited_once_with(
            self.user_identity.organization_id,
            self.user_identity.user_id,
            cache_key,
            value=response,
        )

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_get_user_llm_config_returns_none(self, get_string_cache_key_mock):
        get_string_cache_key_mock.return_value = "user-llm-config:test-key"
        self.cache_mock.get_one.return_value = None

        result = await self.cache_service.get_user_llm_config(
            user_identity=self.user_identity, model_ref_id=self.model_ref_id
        )

        self.assertIsNone(result)
        self.cache_mock.get_one.assert_awaited_once()

    @patch("integration_service.cache.cache_service.get_string_cache_key")
    async def test_user_llm_config_cache_key_uses_model_ref_id(
        self, get_string_cache_key_mock
    ):
        get_string_cache_key_mock.return_value = "user-llm-config:test-key"
        self.cache_mock.get_one.return_value = None

        await self.cache_service.get_user_llm_config(
            user_identity=self.user_identity, model_ref_id=self.model_ref_id
        )

        get_string_cache_key_mock.assert_called_once_with(
            value=str(self.model_ref_id), prefix="user-llm-config"
        )
