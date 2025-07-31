from shared.contracts.ai_orm_context_service import (
    ORMContextRequest, 
    ORMContextResponse, 
    AvailableModelsResponse
)
from clients.base import BaseServiceClient


class AIORMContextClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://ai_orm_context_service:8001') -> None:
        super().__init__(base_url)

    async def get_orm_context(self, payload: ORMContextRequest) -> ORMContextResponse:
        response = await self.post('/v1/ai-orm/get-context', payload)
        return ORMContextResponse(**response.json())
    
    async def get_models(self) -> AvailableModelsResponse:
        response = await self.get('/v1/ai-orm/get-models')
        return AvailableModelsResponse(**response.json())
    