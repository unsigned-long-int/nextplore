from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient

from .vault_key_provider import VaultKeyProvider


class AzureVaultKeyProvider(VaultKeyProvider):
    def __init__(self, key_vault_url: str) -> None:
        self.key_vault_url = key_vault_url

    def create_vault(self, tenant_id: str) -> str:
        cred = DefaultAzureCredential()

        key_client = KeyClient(vault_url=self.key_vault_url, credential=cred)

        key_name = f'kek-{tenant_id}'
        key_size = 3072

        created_key = key_client.create_rsa_key(name=key_name, size=key_size)
        return created_key.id
