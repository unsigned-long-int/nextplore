import unittest
import base64
from unittest.mock import patch, MagicMock

from nextplore_sdk.database.connection_maker.credentials_providers.azure_cert_credentials_provider import \
    AzureCertCredentialsProvider


class TestAzureCertCredentialsProvider(unittest.TestCase):
    def setUp(self):
        self.profile_mock = MagicMock()
        self.credentials_provider = AzureCertCredentialsProvider(self.profile_mock)

    @patch('nextplore_sdk.database.connection_maker.credentials_providers.azure_cert_credentials_provider.CertificateCredential')
    def test_retrieves_cert_with_default_scope(
        self,
        certificate_credential_mock
    ):
        cred_mock = MagicMock()
        token_mock = MagicMock()
        token_mock.token = 'test-token'
        cred_mock.get_token.return_value = token_mock
        certificate_credential_mock.return_value = cred_mock
        with patch.object(self.credentials_provider, '_load_cert') as load_cert_mock:
            load_cert_mock.return_value = 'test-cert'
            creds = self.credentials_provider.creds()

        load_cert_mock.assert_called_once_with()
        certificate_credential_mock.assert_called_once_with(
            tenant_id=self.profile_mock.tenant_id,
            client_id=self.profile_mock.client_id,
            certificate_data='test-cert',
            send_certificate_chain=True
        )
        cred_mock.get_token.assert_called_once_with(self.credentials_provider.DEFAULT_SCOPE)
        self.assertEqual(creds,  'test-token')

    @patch('nextplore_sdk.database.connection_maker.credentials_providers.azure_cert_credentials_provider.CertificateCredential')
    def test_retrieves_cert_with_override_scope(
        self,
        certificate_credential_mock
    ):
        cred_mock = MagicMock()
        token_mock = MagicMock()
        token_mock.token = 'test-token'
        cred_mock.get_token.return_value = token_mock
        certificate_credential_mock.return_value = cred_mock
        with patch.object(self.credentials_provider, '_load_cert') as load_cert_mock:
            load_cert_mock.return_value = 'test-cert'
            _ = self.credentials_provider.creds(scope='custom-scope')
        cred_mock.get_token.assert_called_once_with('custom-scope')

    @patch('nextplore_sdk.database.connection_maker.credentials_providers.azure_cert_credentials_provider.SecretClient')
    def test_byte_encodes_pem(
        self,
        secret_client_cls_mock
    ):
        secret_client_instance = MagicMock()
        secret_mock = MagicMock()
        secret_mock.value = '-----BEGIN CERTIFICATE----- \nMIID...'
        secret_client_instance.get_secret.return_value = secret_mock
        secret_client_cls_mock.return_value = secret_client_instance
        certs = self.credentials_provider._load_cert()
        self.assertEqual(certs, '-----BEGIN CERTIFICATE----- \nMIID...'.encode('utf-8'))

    @patch('nextplore_sdk.database.connection_maker.credentials_providers.azure_cert_credentials_provider.SecretClient')
    def test_byte_encodes_base64(
        self,
        secret_client_cls_mock
    ):
        secret_client_instance = MagicMock()
        secret_mock = MagicMock()
        secret_mock.value = base64.b64encode(b'MIID...').decode('ascii')
        secret_client_instance.get_secret.return_value = secret_mock
        secret_client_cls_mock.return_value = secret_client_instance
        certs = self.credentials_provider._load_cert()
        self.assertEqual(certs, b'MIID...')


