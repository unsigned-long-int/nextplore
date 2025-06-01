import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';

export interface Integration {
    id: string;
    service_type: string;
    connection_name: string;
    database_name: string;
    auth_method: string;
}

export const useIntegrations = () => {
    const { getToken } = useTokenProvider();
    const [ integrations, setIntegrations] = useState<Integration[]>([])
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchIntegrations = async() => {
            try {
                const token = await getToken();
                const response = await axios.get('http://localhost:8000/api/integrations', {
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
        };
        fetchIntegrations();
    }, []);
    return { integrations, loading, error };
}