import axios from 'axios';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useTokenProvider } from '../authentication/useTokenProvider';


export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  organization: string;
  organization_id: string;
}

export const userQuery = async (): Promise<User> => {
    const { getToken } = useTokenProvider();
    const token = await getToken();

    const response = await axios.get('http://localhost:8000/api/me', {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    return response.data;
};