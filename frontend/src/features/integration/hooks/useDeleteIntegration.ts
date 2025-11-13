import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type {ApiError} from '@/shared/api/core/errors';

export const useDeleteIntegration = () => {
    const api = useIntegrationApi();
    const qc = useQueryClient();
    return useMutation<void, ApiError, string>({
        mutationFn: (id: string) => api.deleteIntegration(id),
        mutationKey: ['delete', 'integration'],
        onSuccess: () => qc.invalidateQueries({ queryKey: ['integration-profiles'] })
    });
};