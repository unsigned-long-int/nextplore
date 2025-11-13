import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type {IntegrationUpdateRequest} from '@/shared/api/services/integration/types.gen.ts';
import type { ApiError } from '@/shared/api/core/errors';

type UpdateIntegrationArgs = {
  id: string;
  data: IntegrationUpdateRequest;
};


export const useUpdateIntegration = () => {
    const api = useIntegrationApi();
    return useMutation<void, ApiError, UpdateIntegrationArgs>({
        mutationFn: ({ id, data })=> api.updateIntegration(id, data),
        mutationKey: ['update', 'integration']
    })
}