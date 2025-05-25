export const msalConfig = {
    auth: {
        clientId: 'd873c6f0-0610-4ca2-a843-bb5d8afbaac0',
        authority: 'https://login.microsoftonline.com/8f70164e-3b25-4e26-9938-bea8c8bd314d',
        redirectUri: 'http://localhost:5173/auth/callback',
    },
    cache: {
        cacheLocation: 'localStorage',
        storeAuthStateInCookie: true,
    }
}