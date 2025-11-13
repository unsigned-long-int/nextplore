import { useQuery } from '@tanstack/react-query';
import { useUserApi } from '@/shared/api/services/user/UserApi.ts';

export const useUserStats = () => {
    const api = useUserApi();
    return useQuery({
        queryFn: () => api.getStats(),
        queryKey: ['user-stats'],
    });
};
