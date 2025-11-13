import {
    PublicClientApplication,
    type AccountInfo,
    type AuthenticationResult,
    type SilentRequest,
    type PopupRequest } from '@azure/msal-browser';
import { msalConfig } from './msal-config';

export const msalInstance = new PublicClientApplication(msalConfig);

export const ensureActiveAccount = () => {
    const active = msalInstance.getActiveAccount();
    if (!active) {
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length === 1) msalInstance.setActiveAccount(accounts[0]);
    }
};

const buildSilentRequest = (scopes: string[]): SilentRequest => {
  const account = msalInstance.getActiveAccount();
  return account ? { scopes, account } : { scopes };
};

const buildPopupRequest = (scopes: string[]): PopupRequest => {
  const account = msalInstance.getActiveAccount();
  return account ? { scopes, account } : { scopes };
};

export const acquireToken = async (scopes: string[]): Promise <AuthenticationResult> => {
    ensureActiveAccount();
    try {
        return await msalInstance.acquireTokenSilent(buildSilentRequest(scopes));
    } catch (e) {
        return msalInstance.acquireTokenPopup(buildPopupRequest(scopes));
    }
};

export const login = (scopes: string[]) => {
    return msalInstance.loginPopup({ scopes }).then((res) => {
        msalInstance.setActiveAccount(res.account as AccountInfo);
        return res
    });
};

export const logout = () => {
    const account = msalInstance.getActiveAccount();
    return msalInstance.logoutPopup({ account });
};