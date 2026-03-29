import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type { DataStoreCreateRequest, DataStoreTestResponse } from '@/shared/api/services/integration/types.gen';
import type { ApiError } from '@/shared/api/core/errors';

export const useTestDatastore = () => {
    const api = useIntegrationApi();
    return useMutation<DataStoreTestResponse, ApiError, DataStoreCreateRequest>({
        mutationFn: (data: DataStoreCreateRequest) => api.testDatastore(data),
        mutationKey: ['datastore', 'test'],
    })
}