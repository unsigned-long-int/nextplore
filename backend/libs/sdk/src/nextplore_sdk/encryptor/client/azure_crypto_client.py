import os

from uuid import UUID
from typing import Dict
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys.crypto import CryptographyClient, KeyWrapAlgorithm
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .aad_serializer import serialize_aad
from .crypto_client import CryptoClient
from .encrypted_secret import EncryptedSecret


class AzureCryptoClient(CryptoClient):
    def __init__(self, kek_kid: str) -> None:
        self.crypto_client = CryptographyClient(kek_kid, credential=DefaultAzureCredential())
        self.dek = os.urandom(32)
    
    def encrypt_secret(self, plaintext: str, aad: Dict[str, str | UUID]) -> EncryptedSecret:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.dek)

        aad_bytes = serialize_aad(aad)
        cipher_bytes = aesgcm.encrypt(
            nonce,
            plaintext.encode(),
            aad_bytes
        )
        wrapped_res = self.crypto_client.wrap_key(KeyWrapAlgorithm.rsa_oaep_256, self.dek)
        wrapped_dek = wrapped_res.encrypted_key

        return EncryptedSecret(
            nonce=nonce,
            tag=cipher_bytes[-16:],
            aad=aad,
            ciphertext=cipher_bytes[:-16],
            wrapped_dek=wrapped_dek
        )
    
    def decrypt_secret(
        self,
        wrapped_dek: bytes,
        aad: Dict[str, str | UUID],
        nonce: bytes,
        ciphertext: bytes,
        tag: bytes
    ) -> str:
        unwrapped_res = self.crypto_client.unwrap_key(
            KeyWrapAlgorithm.rsa_oaep_256,
            wrapped_dek
        )
        dek = unwrapped_res.key
        aesgcm = AESGCM(dek)

        aad_bytes = serialize_aad(aad)
        plaintext = aesgcm.decrypt(
            nonce=nonce,
            data=ciphertext + tag,
            associated_data=aad_bytes
        )
        return plaintext.decode()
    