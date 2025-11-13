import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { AIQueryRequest } from '../interface/nextplore_orchestrator/ai-query-request.interface';
import type { AIQueryResponse } from '../interface/nextplore_orchestrator/ai-query-response.interface';


export const useAIQueryRequest = () => {
    const { getToken } = useTokenProvider();

    const getAIQueryResponse = async (request: AIQueryRequest): Promise<AIQueryResponse> => {
        const token = await getToken();

        try {
            const response = await axios.post(
                'http://localhost:8005/v1/nextplore-orchestrator/ai-orm/query',
                request,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    }
                }
            );
            return response.data;
        } catch (e: any) {
            if (axios.isAxiosError(e) && e.response?.data?.detail) {
                const detail = e.response.data.detail;
                throw new Error(
                    typeof detail === 'string'
                        ? detail
                        : detail.message || 'Unknown integration error'
                );
            } else {
                throw new Error('AI query failed unexpectedly');
            }
        }
    };
    return { getAIQueryResponse };
}