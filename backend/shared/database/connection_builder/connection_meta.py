from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ConnectionMeta:
    service_type: str
    auth_method: str
    host: str
    port: int
    database_name: str
    username: Optional[str] = field(default=None)
    password: Optional[str] = field(default=None)
    kerberos_principal: Optional[str] = field(default=None)
    windows_domain: Optional[str] = field(default=None)
    extra_options: Optional[str] = field(default=None)
