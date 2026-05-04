import { useMutation } from '@tanstack/react-query';
import { useOnboardingApi } from '@/shared/api/services/onboarding/OnboardingApi';
import type { ApiError } from '@/shared/api/core/errors';
import type { EmailVerificationResponse, ResendVerificationRequest } from '@/shared/api/services/onboarding/types.gen';


export const useResendVerification = () => {
    const api = useOnboardingApi();
    return useMutation<EmailVerificationResponse, ApiError, ResendVerificationRequest>({
        mutationFn: (data: ResendVerificationRequest) => api.resendVerification(data),
        mutationKey: ['resend-verification'],
    });
};


