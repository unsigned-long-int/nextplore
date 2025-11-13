from typing import Any

from .credentials_provider import CredentialsProvider


class NativePasswordCredentialsProvider(CredentialsProvider):
    def creds(self, **_: Any) -> str:
        return self.profile.password
    