import unittest
import hashlib
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from nextplore_sdk.encryptor.exc.exceptions import AzureCertCreationFailed
from nextplore_sdk.encryptor.cert.cert_generator import Encoding, Cert, logger, x509, CertGenerator


class TestCertGenerator(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(name='FakeCertificateClient')

        p = patch.object(x509, 'load_der_x509_certificate')
        self.addCleanup(p.stop)
        self.mock_x509_loader = p.start()

        p2 = patch('nextplore_sdk.encryptor.cert.cert_generator.logger')
        self.addCleanup(p2.stop)
        self.mock_logger = p2.start()

    def _arrange_success(self, *, not_before):
        der = b'\x01\x02\x03\x04'
        props = type('Props', (), {})()
        props.not_before = not_before
        props.expires_on = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

        cert_obj = type('AKVCert', (), {'properties': props, 'cer': der})()
        poller = MagicMock()
        poller.result.return_value = cert_obj
        self.client.begin_create_certificate.return_value = poller
        self.client.get_certificate.return_value = type('CertProps', (), {'key_id': 'kid-123'})()

        loaded = MagicMock()
        loaded.public_bytes.return_value = b'-----BEGIN CERT-----\n...'
        self.mock_x509_loader.return_value = loaded

        return der, props

    def test_create_cert_success(self):
        der, props = self._arrange_success(
            not_before=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        gen = CertGenerator(cert_name='my-cert', client=self.client)

        res = gen.create_cert()

        self.assertIsInstance(res, Cert)
        self.assertEqual(res.cert_kid, 'kid-123')
        self.assertEqual(res.public_cert_pem, '-----BEGIN CERT-----\n...')
        self.assertEqual(res.thumbprint_sha256, hashlib.sha256(der).hexdigest().upper())
        self.assertEqual(res.not_before, props.not_before)
        self.assertEqual(res.not_after, props.expires_on)

        self.client.begin_create_certificate.assert_called_once()
        self.client.get_certificate.assert_called_once_with('my-cert')

        self.mock_x509_loader.assert_called_once_with(der)
        self.mock_x509_loader.return_value.public_bytes.assert_called_once_with(Encoding.PEM)

    def test_not_before_fallback_to_datetime_now_utc(self):
        self._arrange_success(not_before=None)
        gen = CertGenerator(cert_name='my-cert', client=self.client)

        fixed_now = datetime(2025, 2, 2, 12, 0, 0, tzinfo=timezone.utc)

        class _DTShim:
            @staticmethod
            def now(tz=None):
                return fixed_now

        with patch('nextplore_sdk.encryptor.cert.cert_generator.datetime', new=_DTShim):
            res = gen.create_cert()

        self.assertEqual(res.not_before, fixed_now)

    def test_azure_error_is_wrapped_and_logged(self):
        class FakeAzureError(Exception):
            pass

        with patch('nextplore_sdk.encryptor.cert.cert_generator.AzureError', new=FakeAzureError):
            self.client.begin_create_certificate.side_effect = FakeAzureError('boom')

            gen = CertGenerator(cert_name='bad-cert', client=self.client)

            with self.assertRaises(AzureCertCreationFailed) as ctx:
                gen.create_cert()

            self.assertIn('bad-cert', str(ctx.exception))
            self.assertIn('boom', str(ctx.exception))
            self.mock_logger.error.assert_called()
