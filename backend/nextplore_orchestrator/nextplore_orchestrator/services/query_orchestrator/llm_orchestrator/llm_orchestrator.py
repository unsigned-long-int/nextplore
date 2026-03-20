import logging
from abc import ABC, abstractmethod
from typing import List

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.services.rag import RagPipeline, build_rag_context
from nextplore_orchestrator.services.model_gateway import ModelGateway
from nextplore_orchestrator.services.query_orchestrator.query_executor import QueryExecutor
from nextplore_orchestrator.api.models.ai_query_response import (
    AIQueryResponse,
    PipelineTrace,
    SubQuerySearchResult,
    VectorHit,
    RrfEntry
)
from nextplore_orchestrator.domain.models import RagPipelineResult, RankedVector, VectorNeighbour
from nextplore_orchestrator.domain.mappers import llm_output_specs_dto_from_rag_context
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.services.vector_searcher import VectorSearcher

logger = logging.getLogger(__name__)


class LlmOrchestrator(ABC):
    @abstractmethod
    def run(self, request: AIQueryRequest, user_identity: UserIdentity) -> AIQueryResponse:
        ...


class SimpleLlmOrchestrator(LlmOrchestrator):
    def __init__(
        self,
        vector_search: VectorSearcher,
        model_gateway: ModelGateway,
        query_executor: QueryExecutor,
        top_n: int = 5,
    ) -> None:
        self.vector_search = vector_search
        self.model_gateway = model_gateway
        self.query_executor = query_executor
        self.top_n = top_n

    async def run(self, request: AIQueryRequest, user_identity: UserIdentity) -> AIQueryResponse:
        collection = await self.vector_search.search(request.prompt, user_identity)
        rag_context = build_rag_context(collection.vector_neighbours[:self.top_n])
        orm_context = await self.model_gateway.get_orm_context(request, rag_context, user_identity)
        return await self.query_executor.execute(orm_context, user_identity)

    @staticmethod
    def neighbours_to_ranked(query: str, neighbours: List[VectorNeighbour]) -> List[RankedVector]:
        return [
            RankedVector(vector=vn, rrf_score=vn.score, rank=i, source_queries=[query])
            for i, vn in enumerate(neighbours)
        ]


class ExpandedLlmOrchestrator(LlmOrchestrator):
    def __init__(
        self,
        model_gateway: ModelGateway,
        query_executor: QueryExecutor,
        rag_pipeline: RagPipeline,
    ) -> None:
        self.rag_pipeline = rag_pipeline
        self.model_gateway = model_gateway
        self.query_executor = query_executor

    async def run(self, request: AIQueryRequest, user_identity: UserIdentity) -> AIQueryResponse:
        pipeline = await self.rag_pipeline.run(
            request=request,
            user_identity=user_identity
        )
        llm_output_specs = llm_output_specs_dto_from_rag_context(pipeline.rag_context)
        orm_context = await self.model_gateway.get_orm_context(
            request=request,
            llm_output_specs=llm_output_specs,
            user_identity=user_identity
        )
        response = await self.query_executor.execute(
            orm_context=orm_context,
            user_identity=user_identity
        )
        response.trace = self._build_trace(
            request=request,
            pipeline=pipeline
        )
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