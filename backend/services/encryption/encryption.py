import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

FERNET_KEY = os.getenv('FERNET_KEY')
fernet = Fernet(FERNET_KEY)

def encrypt_secret(secret: str) -> str:
    return fernet.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
