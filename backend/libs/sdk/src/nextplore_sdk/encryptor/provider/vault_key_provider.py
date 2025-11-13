from abc import ABC, abstractmethod


class VaultKeyProvider(ABC):
    @abstractmethod
    def create_vault(self, tenant_id: str) -> None: ...
