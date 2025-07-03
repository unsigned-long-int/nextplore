import axios from 'axios';
import type { AIQueryResponse } from '../interface/ai-query-response.interface';


export const askQuery = async (prompt: string): Promise<AIQueryResponse> => {
  const response = await axios.post('/api/aiquery', {
    prompt,
    db_id: 'demo'
  });
  return response.data;
};