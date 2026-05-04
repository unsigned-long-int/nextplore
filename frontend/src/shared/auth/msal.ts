import {
    PublicClientApplication,
    type AuthenticationResult,
    type SilentRequest,
} from '@azure/msal-browser';
import { msalConfig } from './msal-config';
import { BACKEND_SCOPES } from './scopes';

const CONSENT_ERROR_CODES = [
    'consent_required',
    'interaction_required',
    'admin_consent_required',
    'AADSTS65001',
    'AADSTS90094',
    'AADSTS650052',
    'AADSTS700016',
];

export const msalInstance = new PublicClientApplication(msalConfig);

export const isConsentError = (error: unknown): boolean => {
    const e = error as { errorCode?: string; message?: string };
    const str = `${e?.errorCode ?? ''} ${e?.message ?? ''}`;
    return CONSENT_ERROR_CODES.some(c => str.includes(c));
};

export const getAdminConsentUrl = (tenantId: string): string => {
    const params = new URLSearchParams({
        client_id: import.meta.env.VITE_MSAL_CLIENT_ID,
        redirect_uri: `${window.location.origin}/admin-consent`,
        state: 'admin_consent',
        scope: BACKEND_SCOPES.join(' '),
    });
    return `https://login.microsoftonline.com/${tenantId}/v2.0/adminconsent?${params}`;
};

export const ensureActiveAccount = (): void => {
    if (msalInstance.getActiveAccount()) return;
    const [first] = msalInstance.getAllAccounts();
    if (first) msalInstance.setActiveAccount(first);
};

const buildSilentRequest = (scopes: string[]): SilentRequest => {
    const account = msalInstance.getActiveAccount();
    return account ? { scopes, account } : { scopes };
};

export const acquireToken = async (scopes: string[]): Promise<AuthenticationResult> => {
    ensureActiveAccount();
    try {
        return await msalInstance.acquireTokenSilent(buildSilentRequest(scopes));
    } catch (e) {
        if (isConsentError(e)) throw e;
        await msalInstance.acquireTokenRedirect({ ...buildSilentRequest(scopes) });
        throw e;
    }
};

export const login  = (scopes: string[]) => msalInstance.loginRedirect({ scopes });
export const logout = () => msalInstance.logoutRedirect({
    account: msalInstance.getActiveAccount() ?? undefined,
});