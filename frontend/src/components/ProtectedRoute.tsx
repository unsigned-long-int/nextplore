import { useMsal } from '@azure/msal-react';
import { Navigate } from 'react-router-dom';

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    const { accounts } = useMsal();
    const isAuthenticated = accounts.length > 0;

    return isAuthenticated ? children : <Navigate to="/" />;
};