export type RegisterRequest = {
    company_name: string;
    contact_email: string;
    plan: string;
};

export type RegisterResponse = {
    message: string;
};

export type EmailVerificationResponse = {
    status: string;
};

export type ResendVerificationRequest = {
    contactEmail: string;
};

export type ProfileErrorCode =
    | 'registration_required'
    | 'email_not_verified'
    | 'approval_pending'
    | 'registration_rejected'
    | 'org_suspended';