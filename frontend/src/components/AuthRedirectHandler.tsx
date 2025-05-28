import { AuthenticatedTemplate, UnauthenticatedTemplate } from "@azure/msal-react";

import App from '../App';
import { LoginPage } from '../pages/LoginPage';


export const AuthRedirectHandler: React.FC = () => {
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
