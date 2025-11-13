import { Card, Group, SimpleGrid, Text, ThemeIcon } from '@mantine/core';
import { IconDatabase, IconVector } from '@tabler/icons-react';

import { useUserStats } from '@/features/user/hooks/useUserStats';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';

export const UserStats = () => {
    const { isPending, isError, error, data } = useUserStats();
    if (isPending) return <LoadingOverlay loadingText='Getting user stats...'/>;
    if (isError) return <Text c='red'>{error.message}</Text>;
    if (!data) return <Text>No stats data available.</Text>;

    const user_stats = [
        {
            title: 'Integrations',
            value: data.integrations_number,
            icon: IconDatabase,
            color: 'blue',
        },
        {
            title: 'Vectors',
            value: data.vectors_number,
            icon: IconVector,
            color: 'violet',
        },
    ];

    return (
        <SimpleGrid cols={{ base: 1, sm: 3 }} spacing='lg' mt='md'>
            {user_stats.map((stat) => (
                <Card withBorder radius='md' p='md' key={stat.title} shadow='sm'>
                    <Group justify='space-between'>
                        <div>
                            <Text size='xs' c='dimmed' fw={700}>
                                {stat.title}
                            </Text>
                            <Text fw={700} size='xl'>
                                {stat.value.toLocaleString()}
                            </Text>
                        </div>
                        <ThemeIcon size={40} radius='md' color={stat.color} variant='light'>
                            <stat.icon size={24} />
                        </ThemeIcon>
                    </Group>
                </Card>
            ))}
        </SimpleGrid>
    );
};
