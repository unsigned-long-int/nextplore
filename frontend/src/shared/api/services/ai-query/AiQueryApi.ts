import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type {
    AIQueryResponse,
    AIQueryRequest,
    ModelInfo,
    PromptRequest,
    PromptResponse
} from '@/shared/api/services/ai-query/types.gen';
import type {LlmModelCreateRequest} from "@/shared/api/services/integration/types.gen.ts";


export const useAiQueryApi = () => {
    const http = useOrchestratorClient();
    return {
        getAiResponse: (data: AIQueryRequest) =>
            http.post<AIQueryResponse>('llm-inference/query', data),
        getModels: () =>
            http.get<ModelInfo[]>('llm-inference/models'),
        getDescriptionEnhancement: (data: PromptRequest) =>
            http.post<PromptResponse>('llm-inference/enhancement', data),
        testLlm: (data: LlmModelCreateRequest)=>
            http.post<void>('llm-inference/test', data)
    };
};