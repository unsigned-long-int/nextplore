from enum import Enum


class CertState(Enum):
    PENDING = 'PENDING'
    ASSIGNED = 'ASIGNED'
    ACTIVE = 'ACTIVE'
    REVOKED = 'REVOKED'
    EXPIRED = 'EXPIRED'
    ORPHANED = 'ORPHANED'
