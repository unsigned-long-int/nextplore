import httpx 
from typing import List
from uuid import UUID
from json import JSONDecodeError

from nextplore_orchestrator.clients.base import BaseServiceClient
from .exceptions import ModelResponseRemoteError

from svc_llm_inference_contracts.models import (
    MultiQueryRequest,
    MultiQueryResponse,
    PromptRequest,
    PromptResponse,
    ORMContextResponse,
    ORMContextRequest,
    ModelInfo,
    UserLlmTestRequest
)
from svc_integration_contracts.models import UserLlmCreateRequest




class LlmInferenceClient(BaseServiceClient):
    def __init__(self, base_url: str = 'http://llm_inference_service:8001') -> None:
        super().__init__(base_url)

    async def get_orm_context(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: ORMContextRequest
    ) -> ORMContextResponse:
        try:
            url = f'/v1/llm-inference/organizations/{organization_id}/users/{user_id}/context'
            response = await self.post(url, payload)
            return ORMContextResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (424, 403):
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Structured model response failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Structured model response failed and error response could not be parsed'
                raise ModelResponseRemoteError(message)
            raise 
    
    async def get_platform_models(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> List[ModelInfo]:
        try:
            url = f'/v1/llm-inference/organizations/{organization_id}/users/{user_id}/models'
            response = await self.get(url)
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

    async def get_expanded_query(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: MultiQueryRequest,
    ) -> MultiQueryResponse:
        try:
            url = f'/v1/llm-inference/organizations/{organization_id}/users/{user_id}/query_multiplier'
            response = await self.post(url, payload)
            return MultiQueryResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Multi query model response failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Multi query model response failed and error response could not be parsed'
                raise ModelResponseRemoteError(message)
            raise

    async def get_description_enhancement(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: PromptRequest
    ) -> PromptResponse:
        try:
            url = f'/v1/llm-inference/organizations/{organization_id}/users/{user_id}/chat'
            response = await self.post(url, payload)
            return PromptResponse(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Chat model response failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Chat model response failed and error response could not be parsed'
                raise ModelResponseRemoteError(message)
            raise

    async def test_user_llm(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: UserLlmCreateRequest,
    ) -> None:
        test_request = UserLlmTestRequest(
            model_id=payload.model_id,
            label=payload.label,
            api_base=payload.api_base,
            connection_params=payload.connection_params,
            max_tokens=payload.max_tokens,
        )
        try:
            url = f'/v1/llm-inference/organizations/{organization_id}/users/{user_id}/llm/test'
            response = await self.post(url, test_request)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 424:
                try:
                    detail = e.response.json().get('detail', {})
                    message = detail.get('message', 'Test llm failed')
                except (JSONDecodeError, KeyError, TypeError):
                    message = 'Test llm failed and error response could not be parsed'
                raise ModelResponseRemoteError(message)
            raise