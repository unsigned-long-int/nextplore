import { useMutation } from '@tanstack/react-query';
import { useIntegrationApi } from '@/shared/api/services/integration/IntegrationApi';
import type {DataStoreUpdateRequest} from '@/shared/api/services/integration/types.gen.ts';
import type { ApiError } from '@/shared/api/core/errors';

type UpdateDataStoreArgs = {
  id: string;
  data: DataStoreUpdateRequest;
};


export const useUpdateDatastore = () => {
    const api = useIntegrationApi();
    return useMutation<void, ApiError, UpdateDataStoreArgs>({
        mutationFn: ({ id, data })=> api.updateDatastore(id, data),
        mutationKey: ['update', 'datastore']
    })
}