from typing import Dict

from integration_service.domain.exceptions import MissingCertState
from integration_service.api.models.cert_state import CertState


CERT_STATE_DTO_MAP: Dict[str, CertState] = {
    'PENDING': CertState.PENDING,
    'ASSIGNED': CertState.ASSIGNED,
    'ACTIVE': CertState.ACTIVE,
    'EXPIRED': CertState.EXPIRED,
    'REVOKED': CertState.REVOKED,
    'ORPHANED': CertState.ORPHANED
}


def to_dto_cert_state(cert_state: str) -> CertState:
    try:
        return CERT_STATE_DTO_MAP[cert_state]
    except KeyError:
        raise MissingCertState(f'Cert state not found in map: {cert_state}')