import { createHttp } from '@/shared/api/core/http';
import { useAuth } from '@/app/providers/AuthProvider';

const ACCOUNT_SCOPES = ['openid', 'profile', 'email', import.meta.env.VITE_AAD_SCOPE];
const ORCHESTRATOR_BASE_URL = import.meta.env.VITE_ORCHESTRATOR_BASE_URL;

export const useOrchestratorClient = () => {
    const { getBearer, login } = useAuth();

    return createHttp({
        baseURL: ORCHESTRATOR_BASE_URL,
        scopes: ACCOUNT_SCOPES,
        getBearer,
        onUnauthorized: () => {
            login(ACCOUNT_SCOPES).catch(() => {});
        }
    });
};
