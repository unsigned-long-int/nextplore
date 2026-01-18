from abc import ABC, abstractmethod
from typing import Dict, Any
from svc_ai_orm_context_contracts.models import ORMContextRequest


class BaseProvider(ABC):
    @abstractmethod
    async def retrieve_model_response(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        ...
