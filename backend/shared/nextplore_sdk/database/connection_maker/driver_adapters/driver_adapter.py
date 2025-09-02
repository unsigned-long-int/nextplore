from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class DriverAdapter(ABC):
    @abstractmethod
    def connect(
        self,
        host: str, 
        database: str, 
        port: Optional[int] = None, 
        username: Optional[str] = None, 
        password: Optional[str] = None, 
        ca_path: Optional[str] = None,
        timeout: int = 10,
        attrs_before: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ): ...