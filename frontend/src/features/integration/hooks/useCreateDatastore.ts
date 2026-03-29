import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type { ApiError } from '@/shared/api/core/errors';
import type { DataStoreCreateRequest } from "@/shared/api/services/integration/types.gen.ts";


export const useCreateDatastore = () => {
    const api = useIntegrationApi();
    return useMutation<void, ApiError, DataStoreCreateRequest>({
        mutationFn: (data: DataStoreCreateRequest) => api.createDatastore(data),
        mutationKey: ['datastore', 'create'],
    });
};
