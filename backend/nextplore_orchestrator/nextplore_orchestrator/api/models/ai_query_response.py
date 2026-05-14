from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class VectorHit(BaseModel):
    table: str
    score: float
    snippet: str

class SubQuerySearchResult(BaseModel):
    sub_query: str
    vector_hits: List[VectorHit]

class RrfEntry(BaseModel):
    table: str
    rrf_score: float
    rank: int

class PipelineTrace(BaseModel):
    original_query: str
    sub_queries: List[str]
    vector_hits: List[SubQuerySearchResult]
    rrf_ranking: List[RrfEntry]
    schema_context: List[str]

class AIQueryResponse(BaseModel):
    sql: str
    data: List[Dict[str, str]]
    trace: Optional[PipelineTrace] = Field(None, title="PipelineTrace")
    cache_hit: bool = Field(default=False, title="CacheHit")
