export const CertState = {
    PENDING: 'pending',
    ASSIGNED: 'assigned',
    ACTIVE: 'active',
    REVOKED: 'revoked',
    EXPIRED: 'expired',
    ORPHANED: 'orphaned',
} as const;
export type CertState = typeof CertState[keyof typeof CertState];
