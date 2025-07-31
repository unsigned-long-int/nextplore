import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { ModelInfo } from '../interface/ai-generative-models-response.interface';


export const useAIGenerativeModels = () => {
    const { getToken } = useTokenProvider();

    const getAIGenerativeModels = async (): Promise<ModelInfo[]> => {
        const token = await getToken();

        const response = await axios.get(
            'http://localhost:8005/nextplore-orchestrator/ai-generative-models',
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            }
        );
        return response.data.models;
    };
    return { getAIGenerativeModels };
}