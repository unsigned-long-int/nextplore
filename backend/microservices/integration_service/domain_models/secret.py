from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .secret_type import SecretType


@dataclass
class Secret:
    organization_id: UUID
    user_id: UUID 
    integration_id: UUID
    secret_type: SecretType
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    wrapped_dek: bytes
    kek_kid: str
    aad: bytes
    id: UUID = field(default_factory=uuid4)
    enc_alg: str = field(default='AES-256-GCM')
    wrap_alg: str = field(default='RSA-OAEP-256')
    encoding: str = field(default='utf8')
    version: int = field(default=1)
    