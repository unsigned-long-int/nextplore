import { Avatar, Group, Text } from '@mantine/core';
import { IconAddressBook, IconAt } from '@tabler/icons-react';
import classes from '../styles/UserInfoIcons.module.css';

import { Stats } from '../components/user_profile/UserStats';
import { useUserProfile } from '../hooks/useUserProfile';

export const UserProfilePage = () => {
    const { loading, error, profile } = useUserProfile();
    if (loading) return <Text>Getting user data...</Text>;
    if (error) return <Text c='red'>{error}</Text>;
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
                        <IconAddressBook stroke={1.5} size={16} className={classes.icon} />
                        <Text fz="xs" c="dimmed">
                            {profile.organization}
                        </Text>
                    </Group>
                </div>
            </Group>
            <Group>
                <Stats/>
            </Group>
        </div>
    );
};