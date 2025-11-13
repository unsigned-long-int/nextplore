import axios from 'axios';
import { useCallback } from 'react';
import { useTokenProvider } from '../authentication/useTokenProvider';


export const useIntegrations = () => {
    const { getToken } = useTokenProvider();
    const fetchIntegrations = useCallback(async () => {
        const token = await getToken();
        const response = await axios.get('http://localhost:8005/v1/nextplore-orchestrator/integrations/profiles', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        return response.data;
    }, [getToken]);

    return { fetchIntegrations };
}