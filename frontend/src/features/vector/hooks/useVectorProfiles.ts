import { useQuery } from '@tanstack/react-query';
import { useVectorApi } from '@/shared/api/services/vector/VectorApi.ts';
import type { VectorProfileResponse } from '@/shared/api/services/vector/types.gen.ts';
import type { ApiError } from '@/shared/api/core/errors.ts';

export const useVectorProfiles = (integration_id: string) => {
    const api = useVectorApi();
    return useQuery<VectorProfileResponse[], ApiError>({
        queryFn: ({ queryKey }) => {
            const [, id] = queryKey as [string, string];
            return api.getProfiles(id)
        },
        queryKey: ['vector-profiles', integration_id],
    });
};
