import type { Configuration, PopupRequest } from '@azure/msal-browser';
import { LogLevel } from '@azure/msal-browser';


export const msalConfig: Configuration = {
    auth: {
        clientId: import.meta.env.VITE_MSAL_CLIENT_ID,
        authority: import.meta.env.VITE_MSAL_AUTHORITY,
        redirectUri: import.meta.env.VITE_MSAL_REDIRECT_URI,
        postLogoutRedirectUri: import.meta.env.VITE_MSAL_POST_LOGOUT_REDIRECT_URI
    },
    cache: {
        cacheLocation: 'sessionStorage',
    },
    system: {
        loggerOptions: {
            logLevel: LogLevel.Info,
            piiLoggingEnabled: false,
        }
    }
};


export const loginRequest: PopupRequest = {
    scopes: [
        'openid', 'profile', 'email', 'api://08fc1e2b-9867-42bc-8825-78942fab68da/access_as_user'
    ]
};