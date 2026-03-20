from typing import List

from svc_llm_inference_contracts.models import (
    ChatRequest,
    ORMContextResponse,
    ORMContextRequest,
    LlmOutputSpecs
)
from nextplore_orchestrator.clients.llm_inference import LlmInferenceClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest


class ModelGateway:
    def __init__(
        self,
        llm_inference_client: LlmInferenceClient
    ) -> None:
        self.llm_inference_client = llm_inference_client

    async def expand_query(self, request: AIQueryRequest, user_identity: UserIdentity) -> List[str]:
        response = await self.llm_inference_client.get_chat_response(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            payload=ChatRequest(
                provider=request.provider,
                model_id=request.model_id,
                multiplier=5,
                query=request.prompt,
            ),
        )
        return response.variants

    async def get_orm_context(
        self, request: AIQueryRequest, llm_output_specs: LlmOutputSpecs, user_identity: UserIdentity
    ) -> ORMContextResponse:
        return await self.llm_inference_client.get_orm_context(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            payload=ORMContextRequest(
                provider=request.provider,
                model_id=request.model_id,
                query=request.prompt,
                llm_output_specs=llm_output_specs,
            ),
        )
