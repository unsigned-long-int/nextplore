import {Navigate, useLocation} from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useUserProfile } from '@/features/user/hooks/useUserProfile';
import { ApiError } from '@/shared/api/core/errors.ts';
import type { ProfileErrorCode } from '@/shared/api/services/onboarding/types.gen';
import { isConsentError } from '@/shared/auth/msal.ts';

const ERROR_REDIRECTS: Record<ProfileErrorCode, string> = {
    registration_required: '/register',
    email_not_verified: '/register/check-email',
    approval_pending: '/register/pending',
    registration_rejected: '/register/rejected',
    org_suspended: '/suspended',
};
export const RequireOnboarding = ({ children }: { children: React.ReactNode }) => {
    const { pathname } = useLocation();
    const profile = useUserProfile();

    if (pathname === '/auth-callback') return <>{children}</>;

    if (profile.isLoading) return (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
            <CircularProgress />
        </Box>
    );

    if (profile.isError) {
        const err = profile.error as ApiError;

        if (isConsentError(err))
            return <Navigate to="/admin-consent" replace />;

        const code = (err?.body as { detail?: { code?: string } })?.detail?.code as ProfileErrorCode;
        const redirect = ERROR_REDIRECTS[code];
        if (redirect) return <Navigate to={redirect} replace />;

        throw err;
    }

    return <>{children}</>;
};