from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.keyvault.certificates import (
    CertificateClient,
    CertificatePolicy,
    WellKnownIssuerNames,
    KeyType,
    CertificateContentType
)
from cryptography.hazmat.primitives.serialization import Encoding
from azure.keyvault.secrets import SecretClient
from cryptography import x509


KEK_KID = 'https://nextplore-keyvault.vault.azure.net/keys/kek-8f70164e-3b25-4e26-9938-bea8c8bd314d/4a06015fb28b4765976f7ab806ad4708'

credential = DefaultAzureCredential()
cert_client = CertificateClient(vault_url=KEK_KID, credential=credential)
secret_client = SecretClient(vault_url=KEK_KID, credential=credential)

class CertGenerator:
    def __init__(self, cert_name: str) -> None:
        self.cert_name = cert_name

    def create_cert(self) -> Dict[str, Any]:
        policy = CertificatePolicy(
            issuer_name=WellKnownIssuerNames.self,
            subject='C=DE, O=Nextplore, CN=www.nextplore.co',
            key_size=3072,
            reuse_key=False,
            key_type=KeyType.rsa,
            content_type=CertificateContentType.pkcs12,
            validity_in_months=24,
            exportable=False
        )
        poller = cert_client.begin_create_certificate(
            certificate_name=self.cert_name,
            policy=policy,
            enabled=True
        )
        cert_bundle=poller.result()
        
        der = cert_bundle.cer
        public_pem = x509.load_der_x509_certificate(der).public_bytes(Encoding.PEM).decode()

        key_id = cert_client.get_certificate(self.cert_name).key_id
        return {
            'public_pem': public_pem, 
            'key_id': key_id, 
            'der': der
        }
    