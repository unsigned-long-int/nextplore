import { CertState } from './cert-state.interface';

export interface CertProfile {
    id: string;
    integration_id?: string | null;
    state: CertState
    cert_kid: string;
    public_cert_pem: string;
    thumbprint_sha256: string;
    not_before: Date;
    not_after: Date;
    created_at: Date;
    assigned_at?: Date | null;
    activated_at?: Date | null;
    revoked_at?: Date | null;
};

