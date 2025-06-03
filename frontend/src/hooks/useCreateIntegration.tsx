import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationCreateRequest } from '../interface/integration_create_request';

export const useCreateIntegration = () => {
    const { getToken } = useTokenProvider();

    const createIntegration = async (data: IntegrationCreateRequest) => {
        const token = await getToken();

        const response = await axios.post(
            '/api/createintegration',
            data,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            }
        );
        return response.data;
    };
    return { createIntegration };
};
