import unittest
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch

from utils.encryption.integration_decryptor import decrypt_integration


class TestDecryptIntegration(unittest.TestCase):
    def _make_encrypted(self, **overrides):
        base = {
            'integration_id': uuid4(),
            'organization_id': uuid4(),
            'user_id': uuid4(),
            'service_type': 'postgres',
            'auth_method': 'password',
            'connection_name': 'name',
            'host': 'db.local',
            'port': 5432,
            'database_name': 'analytics',
            'encrypted_username': b'user',
            'encrypted_password': b'pass',
            'encrypted_kerberos_principal': None,
            'encrypted_windows_domain': None,
            'encrypted_extra_options': None,
            'autosync_on': True,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @patch('utils.encryption.integration_decryptor.DecryptedIntegration')
    @patch('utils.encryption.integration_decryptor.decrypt_secret')
    def test_decrypts_present_fields(self, mock_decrypt_secret, mock_dec_cls):
        def dec(val):
            return {
                b'user': 'U',
                b'pass': 'P',
                b'kerb': 'K',
                b'wind': 'W',
                b'extra': 'E',
            }[val]

        mock_decrypt_secret.side_effect = dec
        mock_dec_cls.side_effect = lambda **kw: SimpleNamespace(**kw)

        enc = self._make_encrypted(
            encrypted_username=b'user',
            encrypted_password=b'pass',
            encrypted_kerberos_principal=b'kerb',
            encrypted_windows_domain=b'wind',
            encrypted_extra_options=b'extra',
        )

        out = decrypt_integration(enc)

        self.assertEqual(out.username, 'U')
        self.assertEqual(out.password, 'P')
        self.assertEqual(out.kerberos_principal, 'K')
        self.assertEqual(out.windows_domain, 'W')
        self.assertEqual(out.extra_options, 'E')

        self.assertEqual(out.integration_id, enc.integration_id)
        self.assertEqual(out.organization_id, enc.organization_id)
        self.assertEqual(out.user_id, enc.user_id)
        self.assertEqual(out.service_type, enc.service_type)
        self.assertEqual(out.port, 5432)
        self.assertTrue(out.autosync_on)

        self.assertEqual(mock_decrypt_secret.call_count, 5)

    @patch('utils.encryption.integration_decryptor.DecryptedIntegration')
    @patch('utils.encryption.integration_decryptor.decrypt_secret')
    def test_missing_encrypted_fields_yield_empty_strings(self, mock_decrypt_secret, mock_dec_cls):
        mock_dec_cls.side_effect = lambda **kw: SimpleNamespace(**kw)

        enc = self._make_encrypted(
            encrypted_username=None,
            encrypted_password=None,
            encrypted_kerberos_principal=None,
            encrypted_windows_domain=None,
            encrypted_extra_options=None,
        )

        out = decrypt_integration(enc)

        self.assertEqual(out.username, '')
        self.assertEqual(out.password, '')
        self.assertEqual(out.kerberos_principal, '')
        self.assertEqual(out.windows_domain, '')
        self.assertEqual(out.extra_options, '')

        mock_decrypt_secret.assert_not_called()
