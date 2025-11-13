import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type { AIQueryResponse, AIQueryRequest, ModelInfo } from '@/shared/api/services/ai-query/types.gen';


export const useAiQueryApi = () => {
    const http = useOrchestratorClient();
    return {
        getAiResponse: (data: AIQueryRequest) =>
            http.post<AIQueryResponse>('ai-orm/query', data),
        getModels: () =>
            http.get<ModelInfo[]>('ai-orm/models'),
    };
};