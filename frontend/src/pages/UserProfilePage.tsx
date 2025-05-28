import { IconAt, IconPhoneCall } from '@tabler/icons-react';
import classes from '../styles/UserInfoIcons.module.css';
import { useEffect, useState } from 'react';
import { Avatar, Group, Text } from '@mantine/core';
import type { User } from '../services/user';
import axios from 'axios';
import { useTokenProvider } from '../authentication/useTokenProvider';

export const UserProfilePage = () => {
    const { getToken } = useTokenProvider();
    const [profile, setProfile] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                console.log('getting response')
                const token = await getToken();
                console.log('token', token)
                const response = await axios.get('http://localhost:8000/api/me', {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                console.log(response)
                setProfile(response.data);
            } catch (e) {
                console.log(e);
                setError('Failed to load profile' + e);
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, []);

    if (loading) return <Text>Getting user data...</Text>;
    if (error) return <Text c="red">{error}</Text>;
    if (!profile) return <Text>No user data available.</Text>;

    return (
        <div>
        <Group wrap="nowrap">
            <Avatar
            src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/avatars/avatar-2.png"
            size={94}
            radius="md"
            />
            <div>
            <Text fz="xs" tt="uppercase" fw={700} c="dimmed">
                {profile.role}
            </Text>

            <Text fz="lg" fw={500} className={classes.name}>
                {profile.name}
            </Text>

            <Group wrap="nowrap" gap={10} mt={3}>
                <IconAt stroke={1.5} size={16} className={classes.icon} />
                <Text fz="xs" c="dimmed">
                {profile.email}
                </Text>
            </Group>

            <Group wrap="nowrap" gap={10} mt={5}>
                <IconPhoneCall stroke={1.5} size={16} className={classes.icon} />
                <Text fz="xs" c="dimmed">
                {profile.organization}
                </Text>
            </Group>
            </div>
        </Group>
        </div>
    );
};