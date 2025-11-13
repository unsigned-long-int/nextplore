import axios from 'axios';
import { useCallback, useEffect, useState } from 'react';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { CertProfile } from '../interface/integration/cert-profile.interface';

export const useCertProfiles = () => {
    const { getToken } = useTokenProvider();
    const [certs, setCertProfiles] = useState<CertProfile[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const refetch = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const token = await getToken();
            const response = await axios.get<CertProfile[]>(
                'http://localhost:8005/v1/nextplore-orchestrator/integrations/certificates/profiles',
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            setCertProfiles(response.data);
        } catch (e: any) {
            setError('Failed to load certificates: ' + (e?.message ?? e));
        } finally {
            setLoading(false);
        }
        }, [getToken]);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { loading, error, certs, refetch };
};
