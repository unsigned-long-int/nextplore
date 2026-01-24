from typing import Callable, Dict, Type

from .azure_crypto_client import AzureCryptoClient
from .crypto_client import CryptoClient

CRYPTO_CLIENTS_REGISTRY: Dict[str, Type[CryptoClient]] = {
    'azure': AzureCryptoClient,
}


def get_crypto_client(client: str = 'azure') -> Callable[[str], CryptoClient]:
    crypto_client = CRYPTO_CLIENTS_REGISTRY.get(client)
    return lambda kek_kid: crypto_client(kek_kid)
