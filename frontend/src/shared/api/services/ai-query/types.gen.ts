export type AIQueryRequest = {
    provider: string;
    model_id: string;
    prompt: string;
};

export type AIQueryResponse = {
    sql: string;
    data: { [key: string]: string} [];
};

export type ModelInfo = {
    provider: string;
    model_id: string;
    label: string;
    tags: string[];
};
