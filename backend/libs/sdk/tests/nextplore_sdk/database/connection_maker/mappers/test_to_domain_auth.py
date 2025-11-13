import unittest
from unittest.mock import patch

from nextplore_sdk.database.connection_maker.exc.exceptions import MissingAuth
from nextplore_sdk.database.connection_maker.mappers.to_domain_auth import to_domain_auth

class TestToDomainAuth(unittest.TestCase):
    def setUp(self):
        self.AUTH_MAP_MOCK = patch('nextplore_sdk.database.connection_maker.mappers.to_domain_auth.AUTH_MAP')
        auth_map = {
            'iam': 'IAM',
            'secret': 'SECRET',
            'cert': 'CERT',
            'password_native': 'PASSWORD_NATIVE',
            'password_proxy': 'PASSWORD_PROXY',
            'jwt': 'JWT'
        }
        self.AUTH_MAP_MOCK = self.AUTH_MAP_MOCK.start()
        self.AUTH_MAP_MOCK.__getitem__.side_effect = lambda k: auth_map[k]
        self.addCleanup(self.AUTH_MAP_MOCK.stop)

    def test_to_domain_auth_happy_path(self):
        domain = to_domain_auth('iam')
        self.assertEqual('IAM', domain)

    def test_raises_missing_if_not_found(self):
        with self.assertRaises(MissingAuth) as ctx:
            _ = to_domain_auth('non-existing')
            self.assertIn('Auth not found in map: non-existing', str(ctx.exception))
