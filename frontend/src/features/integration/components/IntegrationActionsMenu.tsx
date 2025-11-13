import { ActionIcon, Menu } from '@mantine/core';
import { IconDots, IconReportAnalytics, IconTrash } from '@tabler/icons-react';

export const IntegrationActionsMenu = ({ onDelete }: { onDelete: () => void }) => (
    <Menu withArrow position='bottom-end' withinPortal>
        <Menu.Target>
        <ActionIcon variant='subtle' color='gray'>
            <IconDots size={16} stroke={1.5} />
        </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
        <Menu.Item leftSection={<IconReportAnalytics size={16} stroke={1.5} />}>Analytics</Menu.Item>
        <Menu.Item leftSection={<IconTrash size={16} stroke={1.5} />} color='red' onClick={onDelete}>
            Delete
        </Menu.Item>
        </Menu.Dropdown>
    </Menu>
    );