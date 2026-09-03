from dataclasses import dataclass, field


@dataclass(frozen=True)
class CertCreate:
    purpose: str | None = field(default=None)
    key_size: int | None = field(default=None)
    validity_in_months: int | None = field(default=None)
