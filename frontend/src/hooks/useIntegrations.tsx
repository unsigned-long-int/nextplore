import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';

export interface IntegrationProfile {
    id: string;
    service_type: string;
    connection_name: string;
    database_name: string;
    auth_method: string;
}

export const useIntegrations = () => {
    const { getToken } = useTokenProvider();
    const [integrations, setIntegrations] = useState<IntegrationProfile[]>([])
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchIntegrations = useCallback(async() => {
        try {
            const token = await getToken();
            const response = await axios.get('/api/integrations', {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            setIntegrations(response.data);
        } catch (e) {
            setError('Failed to load integrations' + e);
        } finally {
            setLoading(false);
        }
    }, []);
    
    useEffect(() => {
        fetchIntegrations()
    },[fetchIntegrations]);

    return { integrations, loading, error, refetch: fetchIntegrations };
}