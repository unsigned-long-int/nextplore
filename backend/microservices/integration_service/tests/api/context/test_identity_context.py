import unittest
import uuid
from contextvars import copy_context

from integration_service.api.context import (
    UserIdentity,
    UserIdentityContextError,
    get_current_identity,
    set_current_identity,
)


class TestIdentityContext(unittest.TestCase):
    def test_none_context(self):
        ctx = copy_context()
        with self.assertRaises(UserIdentityContextError):
            result = ctx.run(get_current_identity)

    def test_set_and_get_identity(self):
        organization_id = uuid.uuid4()
        user_id = uuid.uuid4()

        identity = UserIdentity(organization_id, user_id)

        ctx = copy_context()

        def set_and_get_identity():
            set_current_identity(identity)
            return get_current_identity()

        result = ctx.run(set_and_get_identity)
        self.assertEqual(result.organization_id, organization_id)
        self.assertEqual(result.user_id, user_id)
        self.assertIsInstance(identity, UserIdentity)

    def test_identity_is_isolated_in_context(self):
        user_id1 = uuid.uuid4()
        organization_id1 = uuid.uuid4()
        user_id2 = uuid.uuid4()
        organization_id2 = uuid.uuid4()

        identity1 = UserIdentity(organization_id1, user_id1)
        identity2 = UserIdentity(organization_id2, user_id2)

        ctx1 = copy_context()
        ctx2 = copy_context()

        ctx1.run(set_current_identity, identity1)
        ctx2.run(set_current_identity, identity2)

        result1 = ctx1.run(get_current_identity)
        result2 = ctx2.run(get_current_identity)
        self.assertEqual(result1, identity1)
        self.assertEqual(result2, identity2)
