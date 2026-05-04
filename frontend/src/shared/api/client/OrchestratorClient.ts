import { createHttp } from '@/shared/api/core/http';
import { useAuth } from '@/app/providers/AuthProvider';
import { BACKEND_SCOPES, LOGIN_SCOPES } from '@/shared/auth/scopes';
import {useMemo} from "react";

const ORCHESTRATOR_BASE_URL = import.meta.env.VITE_ORCHESTRATOR_BASE_URL;

export const useOrchestratorClient = () => {
    const {getBearer, login} = useAuth();

    return useMemo(() => createHttp({
        baseURL: ORCHESTRATOR_BASE_URL,
        scopes: BACKEND_SCOPES,
        getBearer,
        onUnauthorized: () => login(LOGIN_SCOPES).catch(console.error),
    }), [getBearer, login]);
}