import axios from 'axios';
import { useEffect, useState } from 'react';

import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationCreateRequest } from '../interface/integration-create-request.interface';

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
                    'http://localhost:8004/nextplore-orchestrator/create-integration',
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
