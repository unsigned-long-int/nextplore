import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.certificates import CertificateClient

AKV_URL = os.getenv("AKV_URL")


def get_cert_client() -> CertificateClient:
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    cert_client = CertificateClient(vault_url=AKV_URL, credential=credential)
    return cert_client
