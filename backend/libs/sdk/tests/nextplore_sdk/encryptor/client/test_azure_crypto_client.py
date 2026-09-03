import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import nextplore_sdk.encryptor.client.azure_crypto_client as mod
from azure.keyvault.keys.crypto import KeyWrapAlgorithm
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TestAzureCryptoClient(unittest.TestCase):
    def setUp(self):
        self.p_cred = patch.object(mod, "DefaultAzureCredential")
        self.mock_cred_cls = self.p_cred.start()
        self.mock_cred = MagicMock(name="DefaultAzureCredential()")
        self.mock_cred_cls.return_value = self.mock_cred

        self.p_crypto_client = patch.object(mod, "CryptographyClient")
        self.mock_crypto_client_cls = self.p_crypto_client.start()
        self.mock_crypto_client = MagicMock(name="CryptographyClient()")
        self.mock_crypto_client_cls.return_value = self.mock_crypto_client

        self._urandom_call = 0
        self._dek = bytes(range(32))
        self._nonce = b"\x01" * 12

        def _urandom(n):
            if self._urandom_call == 0 and n == 32:
                self._urandom_call += 1
                return self._dek
            if self._urandom_call == 1 and n == 12:
                self._urandom_call += 1
                return self._nonce
            return b"\x00" * n

        self.p_urandom = patch.object(mod.os, "urandom", side_effect=_urandom)
        self.p_urandom.start()

        self.addCleanup(self.p_cred.stop)
        self.addCleanup(self.p_crypto_client.stop)
        self.addCleanup(self.p_urandom.stop)

    def test_init_constructs_crypto_client_with_kid_and_credential(self):
        client = mod.AzureCryptoClient("https://kv.vault/keys/mykey/ver")

        self.mock_crypto_client_cls.assert_called_once_with(
            "https://kv.vault/keys/mykey/ver", credential=self.mock_cred
        )
        self.assertEqual(client.dek, self._dek)

    def test_encrypt_secret_structure_and_values(self):
        client = mod.AzureCryptoClient("kid")

        self.mock_crypto_client.wrap_key.return_value = SimpleNamespace(
            encrypted_key=b"WRAPPED"
        )

        plaintext = "s3cr3t"
        aad = {"tenant": "t1", "kid": "123"}
        aad_bytes = json.dumps(aad, separators=(",", ":")).encode()

        expected_full = AESGCM(self._dek).encrypt(
            self._nonce, plaintext.encode(), aad_bytes
        )
        expected_ct = expected_full[:-16]
        expected_tag = expected_full[-16:]

        res = client.encrypt_secret(plaintext, aad)

        self.assertEqual(res.nonce, self._nonce)
        self.assertEqual(res.aad, aad)
        self.assertEqual(res.ciphertext, expected_ct)
        self.assertEqual(res.tag, expected_tag)
        self.assertEqual(res.wrapped_dek, b"WRAPPED")

        self.mock_crypto_client.wrap_key.assert_called_once()
        args, _ = self.mock_crypto_client.wrap_key.call_args
        self.assertEqual(args[0], mod.KeyWrapAlgorithm.rsa_oaep_256)
        self.assertEqual(args[1], self._dek)

    def test_roundtrip_encrypt_then_decrypt(self):
        client = mod.AzureCryptoClient("kid")

        self.mock_crypto_client.wrap_key.return_value = SimpleNamespace(
            encrypted_key=b"WRAPPED"
        )
        self.mock_crypto_client.unwrap_key.return_value = SimpleNamespace(key=self._dek)

        aad = {"tenant": "t1", "kid": "123"}
        plaintext = "top secret value"

        enc = client.encrypt_secret(plaintext, aad)

        out = client.decrypt_secret(
            wrapped_dek=enc.wrapped_dek,
            aad=enc.aad,
            nonce=enc.nonce,
            ciphertext=enc.ciphertext,
            tag=enc.tag,
        )
        self.assertEqual(out, plaintext)

        self.mock_crypto_client.unwrap_key.assert_called_once_with(
            KeyWrapAlgorithm.rsa_oaep_256, enc.wrapped_dek
        )
        args, _ = self.mock_crypto_client.unwrap_key.call_args
        self.assertEqual(args[0], mod.KeyWrapAlgorithm.rsa_oaep_256)
        self.assertEqual(args[1], b"WRAPPED")
