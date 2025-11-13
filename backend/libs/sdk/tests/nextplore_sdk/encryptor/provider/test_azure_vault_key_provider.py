import unittest
from unittest.mock import MagicMock, patch

import nextplore_sdk.encryptor.provider.azure_vault_key_provider as mod

class TestAzureVaultKeyProvider(unittest.TestCase):
    def setUp(self):
        self.p_cred = patch.object(mod, 'DefaultAzureCredential')
        self.mock_cred_cls = self.p_cred.start()

        self.mock_cred = MagicMock(name='DefaultAzureCredential()')
        self.mock_cred_cls.return_value = self.mock_cred

        self.mock_key_client = patch.object(mod, 'KeyClient')
        self.mock_key_client_cls = self.mock_key_client.start()

        self.mock_key_client_instance = MagicMock(name='KeyClient()')
        self.mock_key_client_cls.return_value = self.mock_key_client_instance

        self.mock_created_key = MagicMock(name='created_key')
        self.mock_created_key.id = 'vault-id'
        self.mock_key_client_instance.create_rsa_key.return_value = self.mock_created_key

        self.addCleanup(self.p_cred.stop)
        self.addCleanup(self.mock_key_client.stop)

    def test_creates_vault(self):
        tenant = 'tenant-1'
        azure_vault_key_provider = mod.AzureVaultKeyProvider('test-url')
        vault_id = azure_vault_key_provider.create_vault(tenant)
        self.mock_key_client_cls.assert_called_once_with(
            vault_url='test-url',
            credential=self.mock_cred
        )
        self.mock_key_client_instance.create_rsa_key.assert_called_once_with(name=f'kek-{tenant}', size=3072)
        self.assertEqual(vault_id, self.mock_created_key.id)
