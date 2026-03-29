const CertState = {
    PENDING: 'pending',
    ASSIGNED: 'assigned',
    ACTIVE: 'active',
    REVOKED: 'revoked',
    EXPIRED: 'expired',
    ORPHANED: 'orphaned',
} as const;
export type CertState = typeof CertState[keyof typeof CertState];


export type CertProfile  = {
    id: string;
    datastore_id?: string | null;
    state: CertState;
    cert_kid: string;
    cert_name: string;
    public_cert_pem: string;
    thumbprint_sha256: string;
    not_before: Date;
    not_after: Date;
    created_at: Date;
    assigned_at?: Date | null;
    activated_at?: Date | null;
    revoked_at?: Date | null;
};


export type CertCreateRequest = {
    purpose?: string | null;
    key_size?: number | null;
    validity_in_months?: number | null;
};

