import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationCreateRequest } from '../interface/integration_create_request';

export const useTestIntegration = () => {
    const { getToken } = useTokenProvider();

    const testIntegration = async (data: IntegrationCreateRequest) => {
        const token = await getToken();

        const response = await axios.post(
            '/api/testintegration',
            data,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            }
        );
        return response.data;
    };
    return { testIntegration };
};
