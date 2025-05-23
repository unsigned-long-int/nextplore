import axios from 'axios';

export interface AskQueryResponse {
  sql: string;
  data: any[];
}

export const askQuery = async (prompt: string): Promise<AskQueryResponse> => {
  const response = await axios.post('/api/ask', {
    prompt,
    db_id: 'demo'
  });
  return response.data;
};