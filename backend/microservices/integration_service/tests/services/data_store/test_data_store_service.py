import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from kafka_messaging.events.integration_service import DataStoreCreated
from pydantic import SecretStr
from svc_integration_contracts.models import (
    DB,
    Auth,
    Cloud,
    DataStoreCreateRequest,
    DataStoreUpdateRequest,
)

from integration_service.api.context import UserIdentity
from integration_service.cache import CacheService
from integration_service.database.exceptions import (
    DataStoreCreateFailed,
    DataStoreDeleteFailed,
    DataStoreUpdateFailed,
    KekKidGetFailed,
    SecretsCreateFailed,
)
from integration_service.database.repositories import DataStoreRepository
from integration_service.domain.models.datastore import DataStoreCreate, DataStoreUpdate
from integration_service.domain.models.secret import DataStoreSecret, SecretType
from integration_service.services.data_store import DataStoreService

MODULE = "integration_service.services.data_store.data_store_service"


def make_user_identity(**overrides) -> UserIdentity:
    defaults = {
        "organization_id": uuid4(),
        "user_id": uuid4(),
    }
    return UserIdentity(**{**defaults, **overrides})


def make_create_payload(**overrides) -> DataStoreCreateRequest:
    defaults = {
        "auth": Auth.iam,
        "cloud": Cloud.aws,
        "db": DB.postgresql,
        "connection_name": "test-connection",
        "descr": "test-descr",
        "host": "test.database.windows.net",
        "database_name": "testdb",
        "kek_kid": "https://vault.azure.net/keys/test-key/version",
        "port": 5432,
        "client_secret": SecretStr("secret123"),
    }
    return DataStoreCreateRequest(**{**defaults, **overrides})


def make_update_payload(**overrides) -> DataStoreUpdateRequest:
    defaults = {
        "connection_name": "updated-connection",
        "host": "updated.database.windows.net",
        "port": 5433,
        "database_name": "updated_db",
        "autosync_on": True,
        "client_secret": SecretStr("new-secret"),
    }
    return DataStoreUpdateRequest(**{**defaults, **overrides})


def make_service(
    repo=None, bus=None, cache_service=None, crypto_client_factory=None
) -> DataStoreService:
    mock_cache = MagicMock(spec=CacheService)
    mock_cache.cache = AsyncMock()
    return DataStoreService(
        repo=repo or AsyncMock(spec=DataStoreRepository),
        bus=bus or AsyncMock(),
        cache_service=cache_service or mock_cache,
        crypto_client_factory=crypto_client_factory
        or MagicMock(return_value=MagicMock()),
    )


class TestDataStoreServiceCreate(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_repo = AsyncMock(spec=DataStoreRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client = MagicMock()
        self.mock_crypto_client_factory = MagicMock(
            return_value=self.mock_crypto_client
        )

        self.service = DataStoreService(
            repo=self.mock_repo,
            bus=self.mock_bus,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory,
        )

        self.user_identity = make_user_identity()
        self.organization_id = self.user_identity.organization_id
        self.user_id = self.user_identity.user_id
        self.datastore_id = uuid4()
        self.payload = make_create_payload()
        self.mock_secrets = {SecretType.CLIENT_SECRET: MagicMock(spec=DataStoreSecret)}

    def _setup_success(self, mock_datastore_from_dto, mock_secrets_from_dto):
        mock_datastore_from_dto.return_value = MagicMock(spec=DataStoreCreate)
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.create_datastore.return_value = self.datastore_id

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_creates_datastore(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.create_datastore(self.user_identity, self.payload)
        self.mock_repo.create_datastore.assert_awaited_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            datastore_create=mock_from_dto.return_value,
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_creates_secrets(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.create_datastore(self.user_identity, self.payload)
        self.mock_repo.create_secrets.assert_awaited_once_with(
            organization_id=self.organization_id,
            user_id=self.user_id,
            secrets=self.mock_secrets,
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_publishes_datastore_created_event(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.create_datastore(self.user_identity, self.payload)
        self.mock_bus.publish.assert_awaited_once()
        event = self.mock_bus.publish.call_args.args[0]
        self.assertIsInstance(event, DataStoreCreated)
        self.assertEqual(event.user_id, self.user_id)
        self.assertEqual(event.organization_id, self.organization_id)
        self.assertEqual(event.datastore_id, self.datastore_id)

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_invalidates_cache(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.create_datastore(self.user_identity, self.payload)
        self.mock_cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            self.organization_id, self.user_id
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_uses_correct_kek_kid(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.create_datastore(self.user_identity, self.payload)
        self.mock_crypto_client_factory.assert_called_once_with(self.payload.kek_kid)

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_calls_secrets_from_dto_with_correct_args(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.create_datastore(self.user_identity, self.payload)
        mock_secrets.assert_called_once_with(
            organization_id=self.organization_id,
            datastore_id=self.datastore_id,
            user_id=self.user_id,
            payload=self.payload,
            crypto_client=self.mock_crypto_client,
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_success_call_order(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        call_order = []

        async def track_create_datastore(**kw):
            call_order.append("create_datastore")
            return self.datastore_id

        async def track_create_secrets(**kw):
            call_order.append("create_secrets")

        async def track_publish(*a):
            call_order.append("publish")

        async def track_cache_delete(*a):
            call_order.append("cache_delete")

        self.mock_repo.create_datastore.side_effect = track_create_datastore
        self.mock_repo.create_secrets.side_effect = track_create_secrets
        self.mock_bus.publish.side_effect = track_publish
        self.mock_cache_service.cache.delete_by_prefix.side_effect = track_cache_delete

        await self.service.create_datastore(self.user_identity, self.payload)
        self.assertEqual(
            call_order,
            ["create_datastore", "create_secrets", "publish", "cache_delete"],
        )

    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_datastore_create_failed_raises(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_datastore.side_effect = DataStoreCreateFailed("db error")

        with self.assertRaises(DataStoreCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_datastore_create_failed_no_compensation(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_datastore.side_effect = DataStoreCreateFailed("db error")

        with self.assertRaises(DataStoreCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        self.mock_repo.delete_datastore.assert_not_called()

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_secrets_create_failed_triggers_compensation(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            "encrypt failed"
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        self.mock_repo.delete_datastore.assert_awaited_once_with(
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_id=self.datastore_id,
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_secrets_create_failed_does_not_publish(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            "encrypt failed"
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        self.mock_bus.publish.assert_not_called()

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_secrets_create_failed_does_not_invalidate_cache(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            "encrypt failed"
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_unexpected_error_triggers_compensation(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = RuntimeError("unexpected")

        with self.assertRaises(RuntimeError):
            await self.service.create_datastore(self.user_identity, self.payload)

        self.mock_repo.delete_datastore.assert_awaited_once()

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_datastore_create_failed_logs_error(self, mock_from_dto, mock_logger):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.create_datastore.side_effect = DataStoreCreateFailed("db error")

        with self.assertRaises(DataStoreCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn("Create data store failed", log_call.args[0])
        self.assertTrue(log_call.kwargs["exc_info"])

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_secrets_create_failed_logs_with_context(
        self, mock_from_dto, mock_secrets, mock_logger
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            "encrypt failed"
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        extra = mock_logger.error.call_args.kwargs["extra"]
        self.assertEqual(extra["org_id"], self.organization_id)
        self.assertEqual(extra["user_id"], self.user_id)
        self.assertEqual(extra["error_type"], "SecretsCreateFailed")

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_unexpected_error_logs_with_context(
        self, mock_from_dto, mock_secrets, mock_logger
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = ValueError("unexpected")

        with self.assertRaises(ValueError):
            await self.service.create_datastore(self.user_identity, self.payload)

        extra = mock_logger.error.call_args.kwargs["extra"]
        self.assertEqual(extra["error_type"], "ValueError")

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_compensation_failure_logs_error(
        self, mock_from_dto, mock_secrets, mock_logger
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed(
            "encrypt failed"
        )
        self.mock_repo.delete_datastore.side_effect = DataStoreDeleteFailed(
            "delete failed"
        )

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        log_messages = [c.args[0] for c in mock_logger.error.call_args_list]
        self.assertTrue(any("Compensation failed" in msg for msg in log_messages))

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_create_from_dto")
    async def test_zero_uuid_datastore_id_triggers_compensation(
        self, mock_from_dto, mock_secrets
    ):
        mock_from_dto.return_value = MagicMock()
        mock_secrets.return_value = {}
        self.mock_repo.create_datastore.return_value = UUID(
            "00000000-0000-0000-0000-000000000000"
        )
        self.mock_repo.create_secrets.side_effect = SecretsCreateFailed("failed")

        with self.assertRaises(SecretsCreateFailed):
            await self.service.create_datastore(self.user_identity, self.payload)

        self.mock_repo.delete_datastore.assert_awaited_once()


class TestDataStoreServiceUpdate(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_repo = AsyncMock(spec=DataStoreRepository)
        self.mock_bus = AsyncMock()
        self.mock_cache_service = MagicMock(spec=CacheService)
        self.mock_cache_service.cache = AsyncMock()
        self.mock_crypto_client = MagicMock()
        self.mock_crypto_client_factory = MagicMock(
            return_value=self.mock_crypto_client
        )

        self.service = DataStoreService(
            repo=self.mock_repo,
            bus=self.mock_bus,
            cache_service=self.mock_cache_service,
            crypto_client_factory=self.mock_crypto_client_factory,
        )

        self.user_identity = make_user_identity()
        self.organization_id = self.user_identity.organization_id
        self.user_id = self.user_identity.user_id
        self.datastore_id = uuid4()
        self.kek_kid = "https://vault.azure.net/keys/test-key/version"
        self.payload = make_update_payload()
        self.mock_secrets = {SecretType.CLIENT_SECRET: MagicMock(spec=DataStoreSecret)}

    def _setup_success(self, mock_datastore_update_from_dto, mock_secrets_from_dto):
        mock_datastore_update_from_dto.return_value = MagicMock(spec=DataStoreUpdate)
        mock_secrets_from_dto.return_value = self.mock_secrets
        self.mock_repo.get_kek_kid.return_value = self.kek_kid

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_success_updates_datastore(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.update_datastore(
            self.user_identity, self.datastore_id, self.payload
        )
        self.mock_repo.update_datastore.assert_awaited_once_with(
            datastore_id=self.datastore_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            datastore_update=mock_from_dto.return_value,
            secrets=self.mock_secrets,
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_success_invalidates_cache(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.update_datastore(
            self.user_identity, self.datastore_id, self.payload
        )
        self.mock_cache_service.cache.delete_by_prefix.assert_awaited_once_with(
            self.organization_id, self.user_id
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_success_retrieves_kek_kid(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        await self.service.update_datastore(
            self.user_identity, self.datastore_id, self.payload
        )
        self.mock_repo.get_kek_kid.assert_awaited_once_with(
            datastore_id=self.datastore_id,
            organization_id=self.organization_id,
            user_id=self.user_id,
        )

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_success_uses_retrieved_kek_kid(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        custom_kek = "https://custom.vault.com/keys/k/v2"
        self.mock_repo.get_kek_kid.return_value = custom_kek
        await self.service.update_datastore(
            self.user_identity, self.datastore_id, self.payload
        )
        self.mock_crypto_client_factory.assert_called_once_with(custom_kek)

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_success_call_order(self, mock_from_dto, mock_secrets):
        self._setup_success(mock_from_dto, mock_secrets)
        call_order = []

        async def track_get_kek_kid(**kw):
            call_order.append("get_kek_kid")
            return self.kek_kid

        async def track_update_datastore(**kw):
            call_order.append("update_datastore")

        async def track_cache_delete(*a):
            call_order.append("cache_delete")

        self.mock_repo.get_kek_kid.side_effect = track_get_kek_kid
        self.mock_repo.update_datastore.side_effect = track_update_datastore
        self.mock_cache_service.cache.delete_by_prefix.side_effect = track_cache_delete

        await self.service.update_datastore(
            self.user_identity, self.datastore_id, self.payload
        )
        self.assertEqual(
            call_order, ["get_kek_kid", "update_datastore", "cache_delete"]
        )

    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_kek_kid_get_failed_raises(self, mock_from_dto):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.get_kek_kid.side_effect = KekKidGetFailed("not found")

        with self.assertRaises(KekKidGetFailed):
            await self.service.update_datastore(
                self.user_identity, self.datastore_id, self.payload
            )

        self.mock_repo.update_datastore.assert_not_called()
        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_update_failed_does_not_invalidate_cache(
        self, mock_from_dto, mock_secrets
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.update_datastore.side_effect = DataStoreUpdateFailed(
            "update failed"
        )

        with self.assertRaises(DataStoreUpdateFailed):
            await self.service.update_datastore(
                self.user_identity, self.datastore_id, self.payload
            )

        self.mock_cache_service.cache.delete_by_prefix.assert_not_called()

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_update_failed_logs_with_context(
        self, mock_from_dto, mock_secrets, mock_logger
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.update_datastore.side_effect = DataStoreUpdateFailed("db error")

        with self.assertRaises(DataStoreUpdateFailed):
            await self.service.update_datastore(
                self.user_identity, self.datastore_id, self.payload
            )

        mock_logger.error.assert_called()
        log_call = mock_logger.error.call_args
        self.assertIn("Update data store failed", log_call.args[0])
        extra = log_call.kwargs["extra"]
        self.assertEqual(extra["org_id"], self.organization_id)
        self.assertEqual(extra["user_id"], self.user_id)
        self.assertEqual(extra["datastore_id"], str(self.datastore_id))
        self.assertEqual(extra["error_type"], "DataStoreUpdateFailed")

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_kek_kid_failed_logs_error_type(self, mock_from_dto, mock_logger):
        mock_from_dto.return_value = MagicMock()
        self.mock_repo.get_kek_kid.side_effect = KekKidGetFailed("not found")

        with self.assertRaises(KekKidGetFailed):
            await self.service.update_datastore(
                self.user_identity, self.datastore_id, self.payload
            )

        extra = mock_logger.error.call_args.kwargs["extra"]
        self.assertEqual(extra["error_type"], "KekKidGetFailed")

    @patch(f"{MODULE}.logger")
    @patch(f"{MODULE}.secrets_from_dto")
    @patch(f"{MODULE}.datastore_update_from_dto")
    async def test_unexpected_error_logs_error_type(
        self, mock_from_dto, mock_secrets, mock_logger
    ):
        self._setup_success(mock_from_dto, mock_secrets)
        self.mock_repo.update_datastore.side_effect = ValueError("unexpected")

        with self.assertRaises(ValueError):
            await self.service.update_datastore(
                self.user_identity, self.datastore_id, self.payload
            )

        extra = mock_logger.error.call_args.kwargs["extra"]
        self.assertEqual(extra["error_type"], "ValueError")


class TestCompensateDeleteDataStore(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_repo = AsyncMock(spec=DataStoreRepository)
        self.service = make_service(repo=self.mock_repo)
        self.user_identity = make_user_identity()

    async def test_no_op_when_datastore_id_is_none(self):
        result = await self.service._compensate_delete_datastore(
            user_identity=self.user_identity,
            datastore_id=None,
        )
        self.assertIsNone(result)
        self.mock_repo.delete_datastore.assert_not_called()

    async def test_deletes_when_datastore_id_provided(self):
        datastore_id = uuid4()
        await self.service._compensate_delete_datastore(
            user_identity=self.user_identity,
            datastore_id=datastore_id,
        )
        self.mock_repo.delete_datastore.assert_awaited_once_with(
            user_id=self.user_identity.user_id,
            organization_id=self.user_identity.organization_id,
            datastore_id=datastore_id,
        )

    @patch(f"{MODULE}.logger")
    async def test_logs_error_on_delete_failure(self, mock_logger):
        datastore_id = uuid4()
        self.mock_repo.delete_datastore.side_effect = DataStoreDeleteFailed(
            "delete failed"
        )

        await self.service._compensate_delete_datastore(
            user_identity=self.user_identity,
            datastore_id=datastore_id,
        )

        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        self.assertIn("Compensation failed", log_call.args[0])
        extra = log_call.kwargs["extra"]
        self.assertEqual(extra["org_id"], self.user_identity.organization_id)
        self.assertEqual(extra["user_id"], self.user_identity.user_id)
        self.assertEqual(extra["datastore_id"], str(datastore_id))

    @patch(f"{MODULE}.logger")
    async def test_does_not_reraise_on_delete_failure(self, mock_logger):
        self.mock_repo.delete_datastore.side_effect = DataStoreDeleteFailed(
            "delete failed"
        )

        await self.service._compensate_delete_datastore(
            user_identity=self.user_identity,
            datastore_id=uuid4(),
        )
