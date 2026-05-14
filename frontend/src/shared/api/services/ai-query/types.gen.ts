export type AIQueryRequest = {
    provider: string;
    model_id: string;
    model_ref_id?: string | null;
    is_user_model: boolean;
    prompt: string;
    bypass_cache: boolean;
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
    trace?: PipelineTrace | undefined;
    cache_hit: boolean
};

export const LlmSource = {
    PLATFORM: 'platform',
    USER: 'user'
} as const;
export type LlmSource = typeof LlmSource[keyof typeof LlmSource];

export type LlmProfile = {
    source: LlmSource;
    provider: string;
    model_id: string;
    label: string;
    tags: string[];
    model_ref_id?: string | null;
};

export type PromptRequest = {
    prompt: string;
};

export type PromptResponse = {
    response: string;
};