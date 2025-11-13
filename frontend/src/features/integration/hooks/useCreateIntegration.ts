import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type { ApiError } from '@/shared/api/core/errors';
import type { IntegrationCreateRequest } from "@/shared/api/services/integration/types.gen.ts";


export const useCreateIntegration = () => {
    const api = useIntegrationApi();
    return useMutation<void, ApiError, IntegrationCreateRequest>({
        mutationFn: (data: IntegrationCreateRequest) => api.createIntegration(data),
        mutationKey: ['integration', 'create'],
    });
};
