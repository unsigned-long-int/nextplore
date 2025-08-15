import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { ModelInfo } from '../interface/ai-generative-models-response.interface';


export const useAIGenerativeModels = () => {
    const { getToken } = useTokenProvider();

    const getAIGenerativeModels = async (): Promise<ModelInfo[]> => {
        const token = await getToken();
        try {
            const response = await axios.get(
                'http://localhost:8005/nextplore-orchestrator/ai-generative-models',
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    }
                }
            )
            return response.data.models;
        } catch (e: any) {
            if (axios.isAxiosError(e) && e.response?.data?.detail) {
                const detail = e.response.data.detail;
                throw new Error(
                    typeof detail === 'string'
                        ? detail
                        : detail.message || 'Unknown models error'
                );
            } else {
                throw new Error('Models retrieval failed unexpectedly');
            }
        }
    };
    return { getAIGenerativeModels };
}