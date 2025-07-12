import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationCreateRequest } from '../interface/integration-create-request.interface';

export const useTestIntegration = () => {
    const { getToken } = useTokenProvider();

    const testIntegration = async (data: IntegrationCreateRequest) => {
        const token = await getToken();

        const response = await axios.post(
            '/nextplore-orchestrator/testintegration',
            data,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json', 
                }
            }
        );
        return response.data;
    };
    return { testIntegration };
};
