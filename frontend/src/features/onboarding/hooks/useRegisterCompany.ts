import { useMutation } from '@tanstack/react-query';
import { useOnboardingApi } from '@/shared/api/services/onboarding/OnboardingApi';
import type { ApiError } from '@/shared/api/core/errors';
import type { RegisterRequest, RegisterResponse } from '@/shared/api/services/onboarding/types.gen';


export const useRegisterCompany = () => {
    const api = useOnboardingApi();
    return useMutation<RegisterResponse, ApiError, RegisterRequest>({
        mutationFn: (data: RegisterRequest) => api.registerCompany(data),
        mutationKey: ['onboarding', 'create'],
    });
};


