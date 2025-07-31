import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { IntegrationCreateRequest } from '../interface/integration-create-request.interface';
import type { IntegrationTestResponse } from '../interface/integration-test-response-interface';

export const useTestIntegration = () => {
    const { getToken } = useTokenProvider();

    const testIntegration = async (data: IntegrationCreateRequest): Promise<IntegrationTestResponse> => {
        const token = await getToken();

        const response = await axios.post(
            'http://localhost:8005/nextplore-orchestrator/test-integration',
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
