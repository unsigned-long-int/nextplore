import os
from cryptography.fernet import Fernet

_fernet = None

def _get_fernet():
    global _fernet
    if _fernet is None:
        key = os.getenv('FERNET_KEY')
        if not key:
            raise RuntimeError('FERNET_KEY is not set')
        _fernet = Fernet(key)
    return _fernet


def encrypt_secret(secret: str) -> str:
    return _get_fernet().encrypt(secret.encode()).decode()

def decrypt_secret(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()
