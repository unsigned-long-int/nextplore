import axios from 'axios';
import { useCallback } from 'react';
import { useTokenProvider } from '../authentication/useTokenProvider';

export const useIntegrations = () => {
    const { getToken } = useTokenProvider();
    const fetchIntegrations = useCallback(async () => {
        const token = await getToken();
        const response = await axios.get('http://localhost:8003/nextplore-orchestrator/integrations', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        console.debug(response.data);
        return response.data;
    }, [getToken]);

    return { fetchIntegrations };
}