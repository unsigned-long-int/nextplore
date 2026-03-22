import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type {
    AIQueryResponse,
    AIQueryRequest,
    ModelInfo,
    PromptRequest,
    PromptResponse
} from '@/shared/api/services/ai-query/types.gen';


export const useAiQueryApi = () => {
    const http = useOrchestratorClient();
    return {
        getAiResponse: (data: AIQueryRequest) =>
            http.post<AIQueryResponse>('llm-inference/query', data),
        getModels: () =>
            http.get<ModelInfo[]>('llm-inference/models'),
        getDescriptionEnhancement: (data: PromptRequest) =>
            http.post<PromptResponse>('llm-inference/enhancement', data)
    };
};