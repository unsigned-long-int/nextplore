import unittest
import json
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch

from utils.encryption.integration_encryptor import encrypt_integration


class TestEncryptIntegration(unittest.TestCase):
    def _make_decrypted(self, **overrides):
        base = {
            'organization_id': uuid4(),
            'user_id': uuid4(),
            'service_type': 'postgres',
            'auth_method': 'password',
            'connection_name': 'name',
            'host': 'db.local',
            'port': 5432,
            'database_name': 'analytics',
            'username': 'alice',
            'password': 'secret',
            'kerberos_principal': 'krb',
            'windows_domain': 'ACME',
            'extra_options': {'sslmode': 'require', 'retry': 2},
            'autosync_on': True,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    @patch('utils.encryption.integration_encryptor.EncryptedIntegration')
    @patch('utils.encryption.integration_encryptor.encrypt_secret')
    def test_encrypts_truthy_fields_and_json_extra_options(self, mock_encrypt_secret, mock_enc_cls):
        mock_enc_cls.side_effect = lambda **kw: SimpleNamespace(**kw)

        mock_encrypt_secret.side_effect = lambda s: f'ENC[{s}]'

        dec = self._make_decrypted(
            username='alice',
            password='secret',
            kerberos_principal='krb',
            windows_domain='ACME',
            extra_options={'sslmode': 'require', 'retry': 2},
        )

        out = encrypt_integration(dec)

        self.assertEqual(out.organization_id, dec.organization_id)
        self.assertEqual(out.user_id, dec.user_id)
        self.assertEqual(out.service_type, dec.service_type)
        self.assertEqual(out.auth_method, dec.auth_method)
        self.assertEqual(out.connection_name, dec.connection_name)
        self.assertEqual(out.host, dec.host)
        self.assertEqual(out.port, dec.port)
        self.assertEqual(out.database_name, dec.database_name)
        self.assertTrue(out.autosync_on)

        self.assertEqual(out.encrypted_username, 'ENC[alice]')
        self.assertEqual(out.encrypted_password, 'ENC[secret]')
        self.assertEqual(out.encrypted_kerberos_principal, 'ENC[krb]')
        self.assertEqual(out.encrypted_windows_domain, 'ENC[ACME]')

        calls = mock_encrypt_secret.call_args_list
        extra_opt_arg = calls[-1].args[0]
        self.assertIsInstance(extra_opt_arg, str)
        self.assertEqual(json.loads(extra_opt_arg), dec.extra_options)
        self.assertEqual(out.encrypted_extra_options, f'ENC[{extra_opt_arg}]')

        self.assertEqual(mock_encrypt_secret.call_count, 5)

    @patch('utils.encryption.integration_encryptor.EncryptedIntegration')
    @patch('utils.encryption.integration_encryptor.encrypt_secret')
    def test_falsy_fields_not_encrypted_and_set_to_none(self, mock_encrypt_secret, mock_enc_cls):
        mock_enc_cls.side_effect = lambda **kw: SimpleNamespace(**kw)

        dec = self._make_decrypted(
            username='',
            password=None,
            kerberos_principal='',
            windows_domain=None,
            extra_options={},
        )

        out = encrypt_integration(dec)

        self.assertIsNone(out.encrypted_username)
        self.assertIsNone(out.encrypted_password)
        self.assertIsNone(out.encrypted_kerberos_principal)
        self.assertIsNone(out.encrypted_windows_domain)
        self.assertIsNone(out.encrypted_extra_options)

        mock_encrypt_secret.assert_not_called()
