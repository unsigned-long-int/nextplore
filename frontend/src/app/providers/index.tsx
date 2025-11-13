import {type ReactNode } from 'react';
import { AuthProvider} from './AuthProvider';
import { QueryProvider } from './QueryProvider';


export const AppProviders = ({ children }: { children: ReactNode }) => {
    return (
        <AuthProvider>
            <QueryProvider>{children}</QueryProvider>
        </AuthProvider>
    );
};
