import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type { IntegrationCreateRequest, IntegrationTestResponse } from '@/shared/api/services/integration/types.gen';
import type { ApiError } from '@/shared/api/core/errors';

export const useTestIntegration = () => {
    const api = useIntegrationApi();
    return useMutation<IntegrationTestResponse, ApiError, IntegrationCreateRequest>({
        mutationFn: (data: IntegrationCreateRequest) => api.testIntegration(data),
        mutationKey: ['integration', 'test'],
    })
}