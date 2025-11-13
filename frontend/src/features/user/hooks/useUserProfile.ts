import { useQuery } from '@tanstack/react-query';
import { useUserApi } from '@/shared/api/services/user/UserApi.ts';

export const useUserProfile = () => {
    const api = useUserApi();
    return useQuery({
        queryFn: () => api.getProfile(),
        queryKey: ['user-profile'],
    });
};
