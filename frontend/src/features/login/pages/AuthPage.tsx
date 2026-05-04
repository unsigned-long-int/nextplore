import React from 'react';
import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import App from '@/App';
import { LoginPage } from '@/features/login/pages/LoginPage';
import { RequireOnboarding } from '@/shared/auth/requireOnboarding';
import {useLocation} from "react-router-dom";


export const AuthPage: React.FC = () => {
      const { pathname } = useLocation();

      const isAuthPublicRoute =
        pathname === "/auth-callback" ||
        pathname === "/admin-consent";

      const isAuthenticatedOnboardingRoute =
        pathname === "/register" ||
        pathname.startsWith("/register/") ||
        pathname === "/suspended";

      if (isAuthPublicRoute) {
            return <App />;
      }

      return (
        <>
          <AuthenticatedTemplate>
              {isAuthenticatedOnboardingRoute ? (
                    <App />
              ) : (
                 <RequireOnboarding>
                    <App />
                 </RequireOnboarding>
            )}
            </AuthenticatedTemplate>

            <UnauthenticatedTemplate>
                <LoginPage />
            </UnauthenticatedTemplate>
        </>
      );
};
