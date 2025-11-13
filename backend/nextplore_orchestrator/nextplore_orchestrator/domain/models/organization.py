from dataclasses import dataclass, field


@dataclass(frozen=True)
class Organization:
    azure_tenant_id: str
    name: str
    domain: str
    plan: str = field(default='standard')
