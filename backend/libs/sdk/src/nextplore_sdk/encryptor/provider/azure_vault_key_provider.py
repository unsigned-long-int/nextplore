
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient

from .vault_key_provider import VaultKeyProvider


class AzureVaultKeyProvider(VaultKeyProvider):
    def __init__(
        self, key_vault_url: str, credential: TokenCredential | None = None
    ) -> None:
        self.key_vault_url = key_vault_url
        self._credential = credential or DefaultAzureCredential()
        self._key_client = KeyClient(
            vault_url=self.key_vault_url, credential=self._credential
        )

    def create_vault(self, tenant_id: str) -> str:
        key_name = f"kek-{tenant_id}"
        created_key = self._key_client.create_rsa_key(name=key_name, size=3072)
        return created_key.id
