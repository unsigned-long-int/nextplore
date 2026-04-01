from typing import List

from nextplore_orchestrator.clients.llm_inference import LlmInferenceClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.domain.models import LlmSpec
from nextplore_orchestrator.domain.mappers import user_llm_config_from_llm_spec

from svc_llm_inference_contracts.models import (
    MultiQueryRequest,
    ORMContextResponse,
    ORMContextRequest,
    LlmOutputSpecs
)

class ModelGateway:
    def __init__(
        self,
        llm_inference_client: LlmInferenceClient
    ) -> None:
        self.llm_inference_client = llm_inference_client

    async def expand_query(self, llm_spec: LlmSpec, user_identity: UserIdentity) -> List[str]:
        response = await self.llm_inference_client.get_expanded_query(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            payload=MultiQueryRequest(
                provider=llm_spec.provider,
                model_id=llm_spec.model_id,
                multiplier=5,
                query=llm_spec.prompt,
                user_llm_config=user_llm_config_from_llm_spec(llm_spec)
            ),
        )
        return response.variants

    async def get_orm_context(
        self,  llm_spec: LlmSpec, llm_output_specs: LlmOutputSpecs, user_identity: UserIdentity
    ) -> ORMContextResponse:
        return await self.llm_inference_client.get_orm_context(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            payload=ORMContextRequest(
                provider=llm_spec.provider,
                model_id=llm_spec.model_id,
                query=llm_spec.prompt,
                llm_output_specs=llm_output_specs,
                user_llm_config=user_llm_config_from_llm_spec(llm_spec)
            ),
        )
