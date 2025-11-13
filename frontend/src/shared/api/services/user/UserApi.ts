import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type { UserProfile, UserStats } from '@/shared/api/services/user/types.gen';

export const useUserApi = () => {
    const http = useOrchestratorClient();
    return {
        getStats: () =>
            http.get<UserStats>('users/stats'),
        getProfile: () =>
            http.get<UserProfile>('users/profiles'),
    };
};