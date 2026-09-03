from typing import Any, ClassVar

from azure.identity import ClientSecretCredential

from .credentials_provider import CredentialsProvider


class AzureSecretCredentialsProvider(CredentialsProvider):
    DEFAULT_SCOPE: ClassVar[str] = "https://ossrdbms-aad.database.windows.net/.default"

    def creds(self, **kwargs: Any) -> str:
        scope = kwargs.get("scope") or AzureSecretCredentialsProvider.DEFAULT_SCOPE
        cred = ClientSecretCredential(
            self.profile.tenant_id, self.profile.client_id, self.profile.client_secret
        )

        return cred.get_token(scope).token
