export interface AIQueryResponse {
    sql: string;
    data: { [key: string]: string} [];
};