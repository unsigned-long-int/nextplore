export const LOGIN_SCOPES = ['openid', 'profile', 'email'];

export const BACKEND_SCOPES = [
    `api://${import.meta.env.VITE_AAD_BACKEND_CLIENT_ID}/access_as_user`,
];