import { useState } from 'react';
import {
    IconChevronDown,
    IconBrandSnowflake,
    IconSql,
    IconBrandMysql
} from '@tabler/icons-react';
import { CIcon } from '@coreui/icons-react';
import { cibPostgresql } from '@coreui/icons';
import { Button, Menu, Text, useMantineTheme, Modal } from '@mantine/core';

import { IntegrationForm } from './IntegrationForm';

const INTEGRATIONS = [
    {
      key: 'snowflake',
      label: 'Snowflake',
      icon: (theme: any) => <IconBrandSnowflake size={16} color={theme.colors.blue[6]} stroke={1.5} />,
      shortcut: 'Ctrl + P',
    },
    {
      key: 'sqlserver',
      label: 'SQL Server',
      icon: (theme: any) => <IconSql size={16} color={theme.colors.pink[6]} stroke={1.5} />,
      shortcut: 'Ctrl + T',
    },
    {
      key: 'postgresql',
      label: 'PostgreSQL',
      icon: () => <CIcon icon={cibPostgresql} style={{ width: 16, height: 16 }} />,
      shortcut: 'Ctrl + U',
    },
    {
      key: 'mysql',
      label: 'MySQL',
      icon: (theme: any) => <IconBrandMysql size={16} color={theme.colors.violet[6]} stroke={1.5} />,
      shortcut: 'Ctrl + E',
    },
  ];
  
export const CreateIntegrationButton = () => {
    const theme = useMantineTheme();
    const [modalOpened, setModalOpened] = useState(false);
    const [selectedIntegration, setSelectedIntegration] = useState<string>('');

    const openModalFor = (integrationKey: string) => {
        setSelectedIntegration(integrationKey);
        setModalOpened(true);
      };

    const handleFormSubmit = (data: any) => {
        console.log('Form submitted:', data);
        setModalOpened(false);
      };

    return (
        <>
        <Menu
            transitionProps={{ transition: 'pop-top-right' }}
            position='top-end'
            width={220}
            withinPortal
            radius='md'
        >
            <Menu.Target>
                <Button rightSection={<IconChevronDown size={18} stroke={1.5} />} pr={12} radius='md'>
                    Create new
                </Button>
            </Menu.Target>
            <Menu.Dropdown>
                {INTEGRATIONS.map(({key, label, icon, shortcut}) => (
                    <Menu.Item
                    key={key}
                    leftSection={icon(theme)}
                    rightSection={
                        <Text size='xs' tt='uppercase' fw={700} c='dimmed'>
                            {shortcut}
                        </Text>
                    }
                    onClick={() => openModalFor(key)}
                    >
                        {label}
                    </Menu.Item>
                ))}
            </Menu.Dropdown>
        </Menu>
        <Modal
            opened={modalOpened}
            onClose={() => setModalOpened(false)}
            title={`Create ${selectedIntegration.toUpperCase()} Integration`}
            size='lg'
        >
            <IntegrationForm
                organization_id='your-org-uuid' 
                created_by='user-uuid'
                type={selectedIntegration}
                onSubmit={handleFormSubmit}
            />
        </Modal>
    </>
    );
}