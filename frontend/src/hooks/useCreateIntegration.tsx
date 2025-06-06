import axios from 'axios';
import { useEffect, useState } from 'react';

import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationCreateRequest } from '../interface/integration_create_request';

export const useCreateIntegration = (data: IntegrationCreateRequest) => {
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [response, setResponse] = useState<JSON | null>(null);
    const { getToken } = useTokenProvider();

    useEffect(() => {
        const createIntegration = async (data: IntegrationCreateRequest) => {
            const token = await getToken();
            try {
                const response = await axios.post(
                    '/api/createintegration',
                    data,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        }
                    }
                );
                setResponse(response.data)
            } catch (e) {
                setError('Create integration failed: ' + e);
            } finally {
                setLoading(false);
            };
        };
        createIntegration(data);
    }, []);

    return { error, loading, response };
};
