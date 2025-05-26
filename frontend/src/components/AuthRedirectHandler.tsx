import { AuthenticatedTemplate, UnauthenticatedTemplate } from "@azure/msal-react";

import App from '../App';
import { LoginButton } from "./LoginButton";


export const AuthRedirectHandler: React.FC = () => {

    return (
        <>
            <AuthenticatedTemplate>
                <App/>
            </AuthenticatedTemplate>
            <UnauthenticatedTemplate>
                <LoginButton/>
            </UnauthenticatedTemplate>
        </>
    )
};
