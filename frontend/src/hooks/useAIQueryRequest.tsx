import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { AIQueryResponse } from '../interface/ai-query-response.interface';


export const useAIQueryRequest = () => {
    const { getToken } = useTokenProvider();

    const getAIQueryResponse = async (prompt: string): Promise<AIQueryResponse> => {
        const token = await getToken();

        const response = await axios.post(
            'http://localhost:8003/nextplore-orchestrator/aiquery',
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