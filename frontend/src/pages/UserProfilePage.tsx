import { useEffect, useState } from 'react';
import { Container, Title, Text, Paper } from '@mantine/core';
import { userQuery } from '../services/user';
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
            try{
                const token = await getToken();
                const response = await axios.get('http://localhost:8000/api/me', {
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

    if (loading) return <Text>Loading...</Text>;
    if (error) return <Text color="red">{error}</Text>;
    if (!profile) return <Text>No user data available.</Text>;

    return (
        <Container size="sm" mt="xl">
          <Paper withBorder shadow="md" p="lg">
            <Title order={3} mb="md">
              User Profile
            </Title>
            <Text><strong>Name:</strong> {profile.name}</Text>
            <Text><strong>Email:</strong> {profile.email}</Text>
            <Text><strong>Role:</strong> {profile.role}</Text>
            <Text><strong>Organization:</strong> {profile.organization}</Text>
            <Text><strong>Organization ID:</strong> {profile.organization_id}</Text>
            <Text><strong>User ID:</strong> {profile.id}</Text>
          </Paper>
        </Container>
      );
};
