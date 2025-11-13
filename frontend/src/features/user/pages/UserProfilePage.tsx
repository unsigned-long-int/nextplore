import { Avatar, Group, Text } from '@mantine/core';
import { IconAddressBook, IconAt } from '@tabler/icons-react';

import classes from '@/styles/UserInfoIcons.module.css';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';
import { UserStats } from '@/features/user/components/UserStats';
import { useUserProfile } from '@/features/user/hooks/useUserProfile';

export const UserProfilePage = () => {
    const { isPending, isError, error, data } = useUserProfile();
    if (isPending) return <LoadingOverlay loadingText='Getting user data...'/>;
    if (isError) return <Text c='red'>{error.message}</Text>;
    if (!data) return <Text>No user data available.</Text>;

    return (
        <div>
            <Group wrap='nowrap'>
                <Avatar
                    key={data.name} name={data.name} color='initials'
                    size={94}
                    radius='md'
                />
                <div>
                    <Text fz='xs' tt='uppercase' fw={700} c='dimmed'>
                        {data.role}
                    </Text>
                    <Text fz='lg' fw={500} className={classes.name}>
                        {data.name}
                    </Text>
                    <Group wrap='nowrap' gap={10} mt={3}>
                        <IconAt stroke={1.5} size={16} className={classes.icon} />
                        <Text fz='xs' c='dimmed'>
                            {data.email}
                        </Text>
                    </Group>
                    <Group wrap='nowrap' gap={10} mt={5}>
                        <IconAddressBook stroke={1.5} size={16} className={classes.icon} />
                        <Text fz='xs' c='dimmed'>
                            {data.organization}
                        </Text>
                    </Group>
                </div>
            </Group>
            <Group>
                <UserStats/>
            </Group>
        </div>
    );
};