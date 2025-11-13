import hashlib
import logging
from typing import List, Optional
from datetime import datetime, timezone
from azure.keyvault.certificates import (
    CertificateClient,
    CertificatePolicy,
    WellKnownIssuerNames,
    KeyType,
    CertificateContentType
)
from azure.core.exceptions import AzureError
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography import x509

from nextplore_sdk.encryptor.exc.exceptions import AzureCertCreationFailed
from nextplore_sdk.encryptor.models.cert import Cert
from .get_cert_client import get_cert_client


logger = logging.getLogger(__name__)


class CertGenerator:
    def __init__(
        self,
        cert_name: str,
        client: Optional[CertificateClient] = None,
        hostnames: Optional[List[str]] = None
    ) -> None:
        self.cert_name = cert_name
        self.hostnames = hostnames or ['www.nextplore.co']
        self.cert_client = client or get_cert_client()

    def create_cert(self, key_size: Optional[int] = None, validity_in_months: Optional[int] = None) -> Cert:
        policy = CertificatePolicy(
            issuer_name=WellKnownIssuerNames.self,
            subject='C=DE, O=Nextplore, CN=www.nextplore.co',
            key_size=key_size or 3072,
            reuse_key=False,
            key_type=KeyType.rsa,
            content_type=CertificateContentType.pkcs12,
            validity_in_months=validity_in_months or 24,
            exportable=True
        )
        try:
            poller = self.cert_client.begin_create_certificate(
                certificate_name=self.cert_name,
                policy=policy,
                enabled=True
            )
            cert = poller.result()

            props = cert.properties
            der = cert.cer
            public_pem = x509.load_der_x509_certificate(der).public_bytes(Encoding.PEM).decode()
            thumbprint_sha256 = hashlib.sha256(der).hexdigest().upper()
            not_before = props.not_before or datetime.now(timezone.utc)
            not_after = props.expires_on
            key_id = self.cert_client.get_certificate(self.cert_name).key_id

            return Cert(
                cert_kid=key_id,
                cert_name=self.cert_name,
                public_cert_pem=public_pem,
                thumbprint_sha256=thumbprint_sha256,
                not_before=not_before,
                not_after=not_after
            )
        except AzureError as e:
            logger.error(
                'Certificate creation failed in Azure with error: %s', e,
                exc_info=True
            )
            raise AzureCertCreationFailed(f'Cert creation failed for: {self.cert_name} with error: {e}') from e
