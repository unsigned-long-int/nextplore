import os

from typing import ClassVar, Any
from base64 import b64decode
from azure.identity import CertificateCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from .credentials_provider import CredentialsProvider

AKV_URL = os.getenv('VAULT_URL')
class AzureCertCredentialsProvider(CredentialsProvider):
    DEFAULT_SCOPE: ClassVar[str] = 'https://ossrdbms-aad.database.windows.net/.default'

    def _cert(self) -> str:
        return '/Users/nik/personal_projects/test_connection/app-auth.pem'

    def _load_cert(self) -> bytes:
        sc = SecretClient(
            AKV_URL,
            DefaultAzureCredential()
        )
        s = sc.get_secret(self.profile.azure_cert_kid)
        val = s.value.strip()

        return val.encode("utf-8") if val.startswith("-----BEGIN") else b64decode(val)
    
    def creds(self, **kwargs: Any) -> str:
        scope = kwargs.get('scope', AzureCertCredentialsProvider.DEFAULT_SCOPE)
        cert_bytes = self._load_cert()

        cred = CertificateCredential(
            tenant_id=self.profile.tenant_id, 
            client_id=self.profile.client_id, 
            certificate_path=cert_bytes,
            send_certificate_chain=True,
        )
        return cred.get_token(scope).token
