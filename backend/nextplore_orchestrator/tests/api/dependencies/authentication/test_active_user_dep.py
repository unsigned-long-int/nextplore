import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.dependencies.authentication.active_user_dep import (
    get_active_user,
)

MODULE = "nextplore_orchestrator.api.dependencies.authentication.active_user_dep"


class TestGetActiveUser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.azure_tenant_id = "tenant-abc"
        self.azure_user_id = "user-abc"
        self.azure_user = {"tid": self.azure_tenant_id, "oid": self.azure_user_id}

        self.identity_cache_service = AsyncMock()
        self.backend_connector = MagicMock()

        self.identity = UserIdentity(organization_id=uuid4(), user_id=uuid4())

        set_identity_patcher = patch(f"{MODULE}.set_current_identity")
        self.set_current_identity = set_identity_patcher.start()
        self.addCleanup(set_identity_patcher.stop)

        resolve_patcher = patch(f"{MODULE}.resolve_user_identity")
        self.resolve_user_identity = resolve_patcher.start()
        self.resolve_user_identity.return_value = self.identity
        self.addCleanup(resolve_patcher.stop)

    async def call(self) -> UserIdentity:
        return await get_active_user(
            azure_user=self.azure_user,
            identity_cache_service=self.identity_cache_service,
            backend_connector=self.backend_connector,
        )


class TestCacheHit(TestGetActiveUser):
    def setUp(self):
        super().setUp()
        self.identity_cache_service.get_user_identity.return_value = self.identity

    async def test_returns_the_cached_identity(self):
        result = await self.call()

        self.assertIs(result, self.identity)

    async def test_looks_up_the_cache_with_tid_and_oid(self):
        await self.call()

        self.identity_cache_service.get_user_identity.assert_awaited_once_with(
            self.azure_tenant_id, self.azure_user_id
        )

    async def test_binds_the_cached_identity_to_the_context(self):
        await self.call()

        self.set_current_identity.assert_called_once_with(self.identity)

    async def test_does_not_resolve_or_re_cache_on_a_hit(self):
        await self.call()

        self.resolve_user_identity.assert_not_called()
        self.identity_cache_service.set_user_identity.assert_not_awaited()

    async def test_does_not_touch_the_database_on_a_hit(self):
        await self.call()

        self.backend_connector.session_scope.assert_not_called()


class TestCacheMiss(TestGetActiveUser):
    def setUp(self):
        super().setUp()
        self.identity_cache_service.get_user_identity.return_value = None

    async def test_returns_the_resolved_identity(self):
        result = await self.call()

        self.assertIs(result, self.identity)

    async def test_resolves_using_the_azure_claims_and_connector(self):
        await self.call()

        self.resolve_user_identity.assert_awaited_once_with(
            azure_tenant_id=self.azure_tenant_id,
            azure_user_id=self.azure_user_id,
            backend_connector=self.backend_connector,
        )

    async def test_caches_the_resolved_identity_under_the_azure_claims(self):
        await self.call()

        self.identity_cache_service.set_user_identity.assert_awaited_once_with(
            tid=self.azure_tenant_id,
            oid=self.azure_user_id,
            identity=self.identity,
        )

    async def test_binds_the_resolved_identity_to_the_context(self):
        await self.call()

        self.set_current_identity.assert_called_once_with(self.identity)

    async def test_resolution_failure_propagates_and_does_not_cache(self):
        self.resolve_user_identity.side_effect = RuntimeError("org not found")

        with self.assertRaises(RuntimeError):
            await self.call()

        self.identity_cache_service.set_user_identity.assert_not_awaited()
        self.set_current_identity.assert_not_called()

    async def test_ordering_resolve_then_cache_then_bind(self):
        calls: list[str] = []

        def fake_resolve(**_):
            calls.append("resolve")
            return self.identity

        self.resolve_user_identity.side_effect = fake_resolve
        self.identity_cache_service.set_user_identity.side_effect = lambda **_: (
            calls.append("cache")
        )
        self.set_current_identity.side_effect = lambda *_: calls.append("bind")

        await self.call()

        self.assertEqual(calls, ["resolve", "cache", "bind"])


class TestCacheServiceReturnsFalsyButNotNone(TestGetActiveUser):
    async def test_empty_string_from_cache_is_treated_as_a_miss(self):
        self.identity_cache_service.get_user_identity.return_value = ""

        await self.call()

        self.resolve_user_identity.assert_awaited_once()
