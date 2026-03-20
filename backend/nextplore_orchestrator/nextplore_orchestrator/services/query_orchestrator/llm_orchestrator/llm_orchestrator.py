import logging

from nextplore_orchestrator.services.rag import RagPipeline
from nextplore_orchestrator.services.model_gateway import ModelGateway
from nextplore_orchestrator.services.query_orchestrator.query_executor import QueryExecutor
from nextplore_orchestrator.api.models.ai_query_response import (
    AIQueryResponse,
    PipelineTrace,
    SubQuerySearchResult,
    VectorHit,
    RrfEntry
)
from nextplore_orchestrator.domain.models import RagPipelineResult
from nextplore_orchestrator.domain.mappers import llm_output_specs_dto_from_rag_context
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest


logger = logging.getLogger(__name__)


class AIQueryProcessor:
    def __init__(
        self,
        rag_pipeline: RagPipeline,
        model_gateway: ModelGateway,
        query_executor: QueryExecutor,
    ) -> None:
        self.rag_pipeline = rag_pipeline
        self.model_gateway = model_gateway
        self.query_executor = query_executor

    async def run(self, request: AIQueryRequest) -> AIQueryResponse:
        pipeline = await self.rag_pipeline.run(request)
        llm_output_specs = llm_output_specs_dto_from_rag_context(pipeline.rag_context)
        orm_context = await self.model_gateway.get_orm_context(request, llm_output_specs)
        response = await self.query_executor.execute(orm_context)
        response.trace = self._build_trace(request, pipeline)
        return response

    def _build_trace(self, request: AIQueryRequest, pipeline: RagPipelineResult) -> PipelineTrace:
        return PipelineTrace(
            original_query=request.prompt,
            sub_queries=pipeline.sub_queries,
            vector_hits=[
                SubQuerySearchResult(
                    sub_query=vnc.query,
                    vector_hits=[
                        VectorHit(table=vn.orm_metadata.table_name, score=vn.score, snippet=vn.snippet)
                        for vn in vnc.vector_neighbours
                    ],
                )
                for vnc in pipeline.neighbour_collections
            ],
            rrf_ranking=[
                RrfEntry(table=rv.vector.orm_metadata.table_name, rrf_score=rv.rrf_score, rank=rv.rank)
                for rv in pipeline.ranked
            ],
            schema_context=[entry.vector.orm_metadata.table_name for entry in pipeline.ranked[:self.rag_pipeline.top_n]],
        )