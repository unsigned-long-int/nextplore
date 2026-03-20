from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.services.vector_searcher import VectorSearcher
from nextplore_orchestrator.services.model_gateway import ModelGateway
from nextplore_orchestrator.services.rag import build_rag_context, reciprocal_rank_fusion
from nextplore_orchestrator.domain.models import RagPipelineResult
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest


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

    async def run(self, request: AIQueryRequest, user_identity: UserIdentity) -> RagPipelineResult:
        sub_queries = await self.model_gateway.expand_query(request, user_identity)
        neighbour_collections = await self.vector_search.search_many(sub_queries, user_identity)
        ranked = reciprocal_rank_fusion(neighbour_collections)
        rag_context = build_rag_context([rv.vector for rv in ranked[:self.top_n]])
        return RagPipelineResult(
            sub_queries=sub_queries,
            neighbour_collections=neighbour_collections,
            ranked=ranked,
            rag_context=rag_context,
        )
    
