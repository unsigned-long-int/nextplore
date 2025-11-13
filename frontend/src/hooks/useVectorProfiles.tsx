import axios from 'axios';

import { useTokenProvider } from '../authentication/useTokenProvider';

export const useVectorProfiles = () => {
    const { getToken } = useTokenProvider();

    const fetchVectorProfiles = async(integration_id: string) => {
        const token = await getToken();

        const response = await axios.get(
            `http://localhost:8005/v1/nextplore-orchestrator/integrations/${integration_id}/vectors/profiles`,
            {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    };
    return { fetchVectorProfiles };
}