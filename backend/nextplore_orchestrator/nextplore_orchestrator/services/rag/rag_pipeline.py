import asyncio

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.domain.models import LlmSpec, RagPipelineResult
from nextplore_orchestrator.services.model_gateway import ModelGateway
from nextplore_orchestrator.services.rag import (
    build_rag_context,
    reciprocal_rank_fusion,
)
from nextplore_orchestrator.services.vector_searcher import VectorSearcher


class RagPipeline:
    def __init__(
        self,
        vector_search: VectorSearcher,
        model_gateway: ModelGateway,
        top_n: int = 5,
    ) -> None:
        self.vector_search = vector_search
        self.model_gateway = model_gateway
        self.top_n = top_n

    async def run(
        self, llm_spec: LlmSpec, user_identity: UserIdentity
    ) -> RagPipelineResult:
        sub_queries = await self.model_gateway.expand_query(
            llm_spec=llm_spec, user_identity=user_identity
        )
        var_neighbour_collections, orig_neighbour_collections = await asyncio.gather(
            self.vector_search.search_many(
                queries=sub_queries, user_identity=user_identity
            ),
            self.vector_search.search(
                query=llm_spec.prompt,
                user_identity=user_identity,
                base_prompt_embedding=llm_spec.base_prompt_embedding,
            ),
        )
        neighbour_collections = [*var_neighbour_collections, orig_neighbour_collections]
        ranked = reciprocal_rank_fusion(neighbour_collections)
        rag_context = build_rag_context([rv.vector for rv in ranked[: self.top_n]])
        return RagPipelineResult(
            sub_queries=sub_queries,
            neighbour_collections=neighbour_collections,
            ranked=ranked,
            rag_context=rag_context,
        )
