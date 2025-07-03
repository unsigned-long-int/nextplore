import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { AIQueryResponse } from '../interface/ai-query-response.interface';
import type { AIQueryRequest } from '../interface/ai-query-request.interface';

export const useAIQueryRequest = () => {
    const { getToken } = useTokenProvider();

    const getAIQueryResponse = async (prompt: string): Promise<AIQueryResponse> => {
        const token = await getToken();

        const response = await axios.post(
            '/api/aiquery',
            {
                prompt,
                integration_id: null
            },
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            }
        );
        return response.data;
    };
    return { getAIQueryResponse };
}