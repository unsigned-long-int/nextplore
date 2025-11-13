declare namespace NodeJS {
    interface ProcessEnv {
        MODE_ENV: 'development' | 'production' | 'test';
        MSAL_CLIENT_ID: string;
        MSAL_AUTHORITY: string;
        MSAL_REDIRECT_URI: string;
        MSAL_POST_LOGOUT_REDIRECT_URI: string;
    };
};