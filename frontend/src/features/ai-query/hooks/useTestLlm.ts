import { useMutation } from '@tanstack/react-query';
import type { LlmModelCreateRequest } from '@/shared/api/services/integration/types.gen.ts';
import type { ApiError } from '@/shared/api/core/errors.ts';
import {useAiQueryApi} from "@/shared/api/services/ai-query/AiQueryApi.ts";

export const useTestLlm = () => {
    const api = useAiQueryApi();
    return useMutation<void, ApiError, LlmModelCreateRequest>({
        mutationFn: (data: LlmModelCreateRequest) => api.testLlm(data),
        mutationKey: ['llm', 'test'],
    })
}