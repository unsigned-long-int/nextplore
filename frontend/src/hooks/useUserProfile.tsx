import { useEffect, useState } from 'react';
import { useTokenProvider } from '../authentication/useTokenProvider';
import axios from 'axios';


export interface User {
    id: string;
    email: string;
    name: string;
    role: string;
    organization: string;
    organization_id: string;
  };

export const useUserProfile = () => {
    const { getToken } = useTokenProvider();
    const [profile, setProfile] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const token = await getToken();
                const response = await axios.get('/api/me', {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setProfile(response.data);
            } catch (e) {
                setError('Failed to load profile' + e);
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, []);

    return {loading, error, profile};
};