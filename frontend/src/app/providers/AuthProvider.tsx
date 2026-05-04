import { type ReactNode, createContext, useContext, useMemo } from 'react';
import { MsalProvider, useMsal } from '@azure/msal-react';
import { msalInstance, acquireToken, login, logout } from '@/shared/auth/msal';

type AuthContextValue = {
    isAuthenticated: boolean;
    getBearer: (scopes: string[]) => Promise<string>;
    login: (scopes: string[]) => Promise<void>;
    logout: () => Promise<void>;
};


const AuthContext = createContext<AuthContextValue | null>(null);


export const InnerAuthProvider = ({ children }: { children: ReactNode }) => {
    const { accounts } = useMsal();
    const isAuthenticated = accounts.length > 0;

    const value = useMemo<AuthContextValue>(() => ({
        isAuthenticated,
        async getBearer(scopes: string[]) {
            const res = await acquireToken(scopes);
            return `Bearer ${res.accessToken}`;
        },
        async login(scopes: string[]) {
            await login(scopes);
        },
        async logout() {
            await logout();
        },
    }), [isAuthenticated]);
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    return (
        <MsalProvider instance={msalInstance}>
            <InnerAuthProvider>{children}</InnerAuthProvider>
        </MsalProvider>
    );
};


export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}