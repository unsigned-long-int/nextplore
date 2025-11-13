export const Auth = {
    IAM: 'iam',
    SECRET: 'secret',
    CERT: 'cert',
    PASSWORD_NATIVE: 'password_native',
    PASSWORD_PROXY: 'password_proxy',
    JWT: 'jwt',
} as const;
export type Auth = typeof Auth[keyof typeof Auth];