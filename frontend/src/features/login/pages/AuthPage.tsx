import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';

import App from '@/App';
import { LoginPage } from '@/features/login/pages/LoginPage';


export const AuthPage: React.FC = () => {
    return (
        <>
            <AuthenticatedTemplate>
                <App/>
            </AuthenticatedTemplate>
            <UnauthenticatedTemplate>
                <LoginPage />
            </UnauthenticatedTemplate>
        </>
    )
};
