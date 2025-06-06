import axios from 'axios';

import { useTokenProvider } from '../authentication/useTokenProvider';

export const useIntegrations = () => {
    const { getToken } = useTokenProvider();
    const fetchIntegrations = async() => {
        const token = await getToken();

        const response = await axios.get('/api/integrations', {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    };
    return { fetchIntegrations };
}