import httpx 
from typing import List
from json import JSONDecodeError

from nextplore_orchestrator.clients.ai_orm_context.models.model_info import ModelInfo
from nextplore_orchestrator.clients.ai_orm_context.models.orm_context_request import ORMContextRequest
from nextplore_orchestrator.clients.ai_orm_context.models.orm_context_response import ORMContextResponse
from nextplore_orchestrator.clients.base import BaseServiceClient
from .exceptions import ModelResponseRemoteError


class AIORMContextClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://ai_orm_context_service:8001') -> None:
        super().__init__(base_url)

    async def get_orm_context(self, payload: ORMContextRequest) -> ORMContextResponse:
        try:
            response = await self.post('/v1/ai-orm/context', payload)
            return ORMContextResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Model response failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Model response failed and error response could not be parsed'
                raise ModelResponseRemoteError(message)
            raise 
    
    async def get_models(self) -> List[ModelInfo]:
        try:
            response = await self.get('/v1/ai-orm/models')
            return [ModelInfo(**item) for item in response.json()]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Available models response failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Available models response failed and error response could not be parsed'
                raise ModelResponseRemoteError(message)
            raise
    