import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type {ApiError} from '@/shared/api/core/errors';

export const useDeleteDatastore = () => {
    const api = useIntegrationApi();
    const qc = useQueryClient();
    return useMutation<void, ApiError, string>({
        mutationFn: (id: string) => api.deleteDatastore(id),
        mutationKey: ['delete', 'datastore'],
        onSuccess: () => qc.invalidateQueries({ queryKey: ['data_store-profiles'] })
    });
};