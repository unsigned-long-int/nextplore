import { useQuery } from '@tanstack/react-query';
import { useAiQueryApi } from '@/shared/api/services/ai-query/AiQueryApi';


export const useGetModels = () => {
    const api = useAiQueryApi();
    return useQuery({
        queryFn: () => api.getModels(),
        queryKey: ['ai-models'],
    });
};
