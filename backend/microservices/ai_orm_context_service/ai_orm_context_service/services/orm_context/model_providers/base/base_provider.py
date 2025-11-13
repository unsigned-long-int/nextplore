from abc import ABC, abstractmethod
from typing import Dict, Any

from ai_orm_context_service.api.models.orm_context_request import ORMContextRequest


class BaseProvider(ABC):
    @abstractmethod
    async def retrieve_model_response(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        ...
