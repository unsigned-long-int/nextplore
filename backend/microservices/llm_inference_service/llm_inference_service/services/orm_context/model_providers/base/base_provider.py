from abc import ABC, abstractmethod
from typing import Dict, Any
from svc_ai_orm_context_contracts.models import ORMContextRequest


class BaseProvider(ABC):
    @abstractmethod
    async def execute_structured_query(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def execute_query(self, query: str) -> str:
        ...