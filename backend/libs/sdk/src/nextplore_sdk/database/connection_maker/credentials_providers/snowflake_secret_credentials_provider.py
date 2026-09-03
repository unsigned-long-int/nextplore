from typing import Any

from .credentials_provider import CredentialsProvider


class SnowflakeSecretCredentialsProvider(CredentialsProvider):
    def creds(self, **_: Any) -> str:
        return self._secret()

    def _secret(self) -> str:
        return self.profile.client_secret
