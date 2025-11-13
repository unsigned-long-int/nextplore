from typing import Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CertCreate:
    purpose: Optional[str] = field(default=None)
    key_size: Optional[int] = field(default=None)
    validity_in_months: Optional[int] = field(default=None)
