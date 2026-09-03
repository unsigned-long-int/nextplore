import asyncio
import contextvars
import unittest
from contextvars import Token
from dataclasses import FrozenInstanceError
from uuid import uuid4

from nextplore_sdk.identity.context import (
    UserIdentity,
    UserIdentityContextError,
    current_identity,
    get_current_identity,
    identity_context,
    set_current_identity,
)


def make_identity() -> UserIdentity:
    return UserIdentity(organization_id=uuid4(), user_id=uuid4())


class IdentityContextTestBase(unittest.TestCase):
    def setUp(self):
        token = identity_context.set(None)
        self.addCleanup(identity_context.reset, token)


class TestSetAndGet(IdentityContextTestBase):
    def test_round_trip(self):
        identity = make_identity()

        set_current_identity(identity)

        self.assertIs(get_current_identity(), identity)

    def test_raises_when_nothing_is_set(self):
        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

    def test_error_message_is_descriptive(self):
        with self.assertRaises(UserIdentityContextError) as ctx:
            get_current_identity()

        self.assertIn("not found in context", str(ctx.exception))

    def test_second_set_replaces_the_first(self):
        first, second = make_identity(), make_identity()

        set_current_identity(first)
        set_current_identity(second)

        self.assertIs(get_current_identity(), second)

    def test_setting_none_clears_the_identity(self):
        set_current_identity(make_identity())
        set_current_identity(None)

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

    def test_set_returns_a_token(self):
        token = set_current_identity(make_identity())

        self.assertIsInstance(token, Token)

    def test_token_restores_the_previous_value(self):
        first, second = make_identity(), make_identity()
        set_current_identity(first)

        token = set_current_identity(second)
        self.assertIs(get_current_identity(), second)

        identity_context.reset(token)
        self.assertIs(get_current_identity(), first)

    def test_get_never_returns_none(self):
        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

        set_current_identity(make_identity())
        self.assertIsNotNone(get_current_identity())


class TestCurrentIdentityContextManager(IdentityContextTestBase):
    def test_binds_inside_the_block(self):
        identity = make_identity()

        with current_identity(identity):
            self.assertIs(get_current_identity(), identity)

    def test_yields_the_identity(self):
        identity = make_identity()

        with current_identity(identity) as bound:
            self.assertIs(bound, identity)

    def test_restores_absence_after_the_block(self):
        with current_identity(make_identity()):
            pass

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

    def test_restores_the_previous_identity_after_the_block(self):
        outer, inner = make_identity(), make_identity()
        set_current_identity(outer)

        with current_identity(inner):
            self.assertIs(get_current_identity(), inner)

        self.assertIs(get_current_identity(), outer)

    def test_restores_even_when_the_block_raises(self):
        outer = make_identity()
        set_current_identity(outer)

        with self.assertRaises(ValueError), current_identity(make_identity()):
            raise ValueError("boom")

        self.assertIs(get_current_identity(), outer)

    def test_nests_correctly(self):
        first, second, third = make_identity(), make_identity(), make_identity()

        with current_identity(first):
            with current_identity(second):
                with current_identity(third):
                    self.assertIs(get_current_identity(), third)
                self.assertIs(get_current_identity(), second)
            self.assertIs(get_current_identity(), first)

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()


class TestContextIsolation(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_tasks_keep_their_own_identity(self):
        first, second = make_identity(), make_identity()

        async def run_with(identity: UserIdentity) -> UserIdentity:
            set_current_identity(identity)
            await asyncio.sleep(0)
            return get_current_identity()

        results = await asyncio.gather(run_with(first), run_with(second))

        self.assertIs(results[0], first)
        self.assertIs(results[1], second)

    async def test_fifty_concurrent_tasks_stay_isolated(self):
        identities = [make_identity() for _ in range(50)]

        async def run_with(identity: UserIdentity) -> bool:
            with current_identity(identity):
                await asyncio.sleep(0)
                return get_current_identity() is identity

        results = await asyncio.gather(
            *(asyncio.create_task(run_with(i)) for i in identities)
        )

        self.assertTrue(all(results))

    async def test_child_task_inherits_the_parent_identity(self):
        identity = make_identity()
        set_current_identity(identity)

        async def child() -> UserIdentity:
            return get_current_identity()

        self.assertIs(await asyncio.create_task(child()), identity)

    async def test_child_task_set_does_not_leak_to_the_parent(self):
        async def child() -> None:
            set_current_identity(make_identity())

        await asyncio.create_task(child())

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

    async def test_identity_propagates_into_to_thread(self):
        identity = make_identity()
        set_current_identity(identity)

        def in_thread() -> UserIdentity:
            return get_current_identity()

        self.assertIs(await asyncio.to_thread(in_thread), identity)

    async def test_sequential_awaits_share_one_context(self):
        identity = make_identity()

        async def setter() -> None:
            set_current_identity(identity)

        async def getter() -> UserIdentity:
            return get_current_identity()

        await setter()

        self.assertIs(await getter(), identity)


class TestCopiedContext(unittest.TestCase):
    def test_copy_context_run_is_isolated(self):

        def inner() -> None:
            set_current_identity(make_identity())

        contextvars.copy_context().run(inner)

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

    def test_default_is_none_in_a_fresh_context(self):
        self.assertIsNone(contextvars.copy_context().run(identity_context.get))


class TestUserIdentity(unittest.TestCase):
    def test_is_frozen(self):
        identity = make_identity()

        with self.assertRaises(FrozenInstanceError):
            identity.user_id = uuid4()

    def test_equality_is_by_value(self):
        org_id, user_id = uuid4(), uuid4()

        self.assertEqual(
            UserIdentity(organization_id=org_id, user_id=user_id),
            UserIdentity(organization_id=org_id, user_id=user_id),
        )

    def test_is_hashable(self):
        identity = make_identity()
        self.assertEqual({identity: "value"}[identity], "value")
