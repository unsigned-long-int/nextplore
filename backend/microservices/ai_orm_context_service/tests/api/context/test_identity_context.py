import unittest
from contextvars import copy_context

from api.context import set_current_identity, get_current_identity
from nextplore_sdk.identity_service.identity_model.user_identity import UserIdentity


class TestIdentityContext(unittest.TestCase):
    def test_default_identity_is_none(self):
        ctx = copy_context()
        result = ctx.run(get_current_identity)
        self.assertIsNone(result)
    
    def test_set_and_get_identity(self):
        identity = UserIdentity(user_id='abc123', organization_id='test-org')

        ctx = copy_context()
        def set_and_get():
            set_current_identity(identity)
            return get_current_identity()
        
        result = ctx.run(set_and_get)
        self.assertEqual(result, identity)
        self.assertEqual(result.user_id, 'abc123')
        self.assertEqual(result.organization_id, 'test-org')

    def test_identity_is_isolated_in_contexts(self):
        identity1 = UserIdentity(user_id='user1', organization_id='test-org')
        identity2 = UserIdentity(user_id='user2', organization_id='test-org')

        ctx1 = copy_context()
        ctx2 = copy_context()

        ctx1.run(set_current_identity, identity1)
        ctx2.run(set_current_identity, identity2)

        result1 = ctx1.run(get_current_identity)
        result2 = ctx2.run(get_current_identity)

        self.assertEqual(result1.user_id, 'user1')
        self.assertEqual(result2.user_id, 'user2')
