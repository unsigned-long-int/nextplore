import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type { ApiError } from '@/shared/api/core/errors';
import type { LlmModelCreateRequest } from "@/shared/api/services/integration/types.gen.ts";


export const useCreateLlm = () => {
    const api = useIntegrationApi();
    return useMutation<void, ApiError, LlmModelCreateRequest>({
        mutationFn: (data: LlmModelCreateRequest) => api.createLlm(data),
        mutationKey: ['llm', 'create'],
    });
};
