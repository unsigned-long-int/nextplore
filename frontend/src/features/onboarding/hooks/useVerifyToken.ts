import { useQuery } from '@tanstack/react-query';
import { useOnboardingApi } from '@/shared/api/services/onboarding/OnboardingApi';

export const useVerifyToken = (token: string) => {
    const api = useOnboardingApi();
    return useQuery({
        queryKey: ['verification-token', token],
        queryFn: () => api.verifyToken(token),
        enabled: !!token,
        retry: false,
    });
};


