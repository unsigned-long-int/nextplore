import { useEffect, useState } from 'react';
import axios from 'axios';

import { useTokenProvider } from '../authentication/useTokenProvider';
import type { UserProfile } from '../interface/user-profile.interface';



export const useUserProfile = () => {
    const { getToken } = useTokenProvider();
    const [profile, setProfile] = useState<UserProfile | null>(null);
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