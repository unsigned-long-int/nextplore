import { LogLevel } from '@azure/msal-browser';
import type { PopupRequest, Configuration } from '@azure/msal-browser';

export const msalConfig: Configuration = {
    auth: {
        clientId: '58aac92c-e335-4993-ba1f-f21583db5501',
        authority: 'https://login.microsoftonline.com/8f70164e-3b25-4e26-9938-bea8c8bd314d/v2.0',
        redirectUri: 'http://localhost:5173/auth-callback',
        postLogoutRedirectUri: 'http://localhost:5173'
    },
    cache: {
        cacheLocation: 'sessionStorage',
        storeAuthStateInCookie: true,
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