import { useOrchestratorClient } from '@/shared/api/client/OrchestratorClient';
import type {
    RegisterRequest,
    RegisterResponse,
    EmailVerificationResponse,
    ResendVerificationRequest

} from '@/shared/api/services/onboarding/types.gen';


export const useOnboardingApi = () => {
    const http = useOrchestratorClient();

    return {
        registerCompany: (data: RegisterRequest) =>
            http.post<RegisterResponse>('organizations/register', data),
        verifyToken: (token: string) =>
            http.get<EmailVerificationResponse>(`organizations/register/verify?token=${token}`),
        resendVerification: (data: ResendVerificationRequest) =>
            http.post<EmailVerificationResponse>('organizations/register/resend-verification', data),
    };
};