from pydantic import BaseModel, Field


class VectorHit(BaseModel):
    table: str
    score: float
    snippet: str


class SubQuerySearchResult(BaseModel):
    sub_query: str
    vector_hits: list[VectorHit]


class RrfEntry(BaseModel):
    table: str
    rrf_score: float
    rank: int


class PipelineTrace(BaseModel):
    original_query: str
    sub_queries: list[str]
    vector_hits: list[SubQuerySearchResult]
    rrf_ranking: list[RrfEntry]
    schema_context: list[str]


class AIQueryResponse(BaseModel):
    sql: str
    data: list[dict[str, str]]
    trace: PipelineTrace | None = Field(None, title="PipelineTrace")
    cache_hit: bool = Field(default=False, title="CacheHit")
