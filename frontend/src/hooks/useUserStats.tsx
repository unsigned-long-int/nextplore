import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTokenProvider } from '../authentication/useTokenProvider';
import type { UserStats } from '../interface/user-stats.interface';


export const useUserStats = () => {
    const { getToken } = useTokenProvider();
    const [stats, setStats] = useState<UserStats | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const token = await getToken();
                const response = await axios.get('/nextplore-orchestrator/userstats', {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setStats(response.data);
            } catch (e) {
                setError('Failed to load stats' + e);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    return {loading, error, stats};
}
