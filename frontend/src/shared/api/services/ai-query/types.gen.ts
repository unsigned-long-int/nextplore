export type AIQueryRequest = {
    provider: string;
    model_id: string;
    prompt: string;
};

export type VectorHit = {
    table: string;
    score: number;
    snippet: string;
}

export type SubQuerySearchResult = {
    sub_query: string;
    vector_hits: VectorHit[];
}

export type RrfEntry = {
    table: string;
    rrf_score: number;
    rank: number;
}

export type PipelineTrace = {
    original_query: string;
    sub_queries: string[];
    vector_hits: SubQuerySearchResult[];
    rrf_ranking: RrfEntry[];
    schema_context: string[];
}

export type AIQueryResponse = {
    sql: string;
    data: { [key: string]: string} [];
    trace?: PipelineTrace | undefined
};

export type ModelInfo = {
    provider: string;
    model_id: string;
    label: string;
    tags: string[];
};
