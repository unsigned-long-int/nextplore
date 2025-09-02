import os
import json

from typing import Dict
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys.crypto import CryptographyClient, KeyWrapAlgorithm
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .encrypted_secret import EncryptedSecret


class CryptoClient:
    def __init__(self, kek_kid: str) -> None:
        self.crypto_client = CryptographyClient(kek_kid, credential=DefaultAzureCredential())
        self.dek = os.urandom(32)
    
    def encrypt_secret(self, plaintext: str, aad: Dict[str, str]) -> EncryptedSecret:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.dek)

        aad_bytes = json.dumps(aad, separators=(',', ':')).encode()
        cipher_bytes = aesgcm.encrypt(
            nonce,
            plaintext.encode(),
            aad_bytes
        )
        wrapped_res = self.crypto_client.wrap_key(KeyWrapAlgorithm.rsa_oaep_256, self.dek)
        wrapped_dek = wrapped_res.encrypted_key

        return EncryptedSecret(
            nonce=nonce,
            tag = cipher_bytes[-16:],
            aad=aad_bytes,
            ciphertext=cipher_bytes[:-16],
            wrapped_dek=wrapped_dek
        )
    
    def decrypt_secret(self, encrypted_secret: EncryptedSecret) -> str:
        unwrapped_res = self.crypto_client.unwrap_key(
            KeyWrapAlgorithm.rsa_oaep_256,
            encrypted_secret.wrapped_dek
        )
        dek = unwrapped_res.key
        aesgcm = AESGCM(dek)

        plaintext = aesgcm.decrypt(
            encrypted_secret.nonce,
            encrypted_secret.ciphertext + encrypted_secret.tag,
            aad=encrypted_secret.aad
        )
        return plaintext.decode()
    