import { cibPostgresql } from "@coreui/icons";
import { CIcon } from "@coreui/icons-react";
import { Button, Menu, Modal, Text, useMantineTheme } from "@mantine/core";
import { showNotification } from '@mantine/notifications';
import {
    IconBrandMysql,
    IconBrandSnowflake,
    IconCheck,
    IconChevronDown,
    IconSql,
    IconX,
} from "@tabler/icons-react";
import axios from "axios";
import { useState } from "react";

import { useTokenProvider } from "../../authentication/useTokenProvider";
import type { IntegrationCreateRequest } from "../../interface/integration-create-request.interface";
import type { IntegrationCreateResponse } from "../../interface/integration-create-response-interface";
import { IntegrationForm } from "./IntegrationForm";

const INTEGRATIONS = [
    {
        key: "snowflake",
        label: "Snowflake",
        icon: (theme: any) => (
        <IconBrandSnowflake size={16} color={theme.colors.blue[6]} stroke={1.5} />
        ),
        shortcut: "Ctrl + P",
    },
    {
        key: "sqlserver",
        label: "SQL Server",
        icon: (theme: any) => (
        <IconSql size={16} color={theme.colors.pink[6]} stroke={1.5} />
        ),
        shortcut: "Ctrl + T",
    },
    {
        key: "postgresql",
        label: "PostgreSQL",
        icon: () => (
        <CIcon icon={cibPostgresql} style={{ width: 16, height: 16 }} />
        ),
        shortcut: "Ctrl + U",
    },
    {
        key: "mysql",
        label: "MySQL",
        icon: (theme: any) => (
        <IconBrandMysql size={16} color={theme.colors.violet[6]} stroke={1.5} />
        ),
        shortcut: "Ctrl + E",
    },
];

export const createIntegration = async (
    data: IntegrationCreateRequest,
    token: string | null
): Promise<IntegrationCreateResponse> => {
    const response = await axios.post("http://localhost:8005/nextplore-orchestrator/create-integration", data, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    return response.data;
};

export const CreateIntegrationButton = () => {
    const theme = useMantineTheme();
    const [modalOpened, setModalOpened] = useState(false);
    const [selectedIntegration, setSelectedIntegration] = useState<string>("");
    const { getToken } = useTokenProvider();

    const openModalFor = (integrationKey: string) => {
            setSelectedIntegration(integrationKey);
            setModalOpened(true);
    };

    const handleFormSubmit = async (data: IntegrationCreateRequest) => {
        const token = await getToken();
        const result = await createIntegration(data, token);
        try {
            if (!result.success) throw new Error(!result.message ? 'Unhandled Error': result.message);
            showNotification({
                title: 'Integration Created',
                message: `${data.connection_name} was successfully created and will be vectorized`,
                icon: <IconCheck size={16} />, color: 'green'
            });
            setModalOpened(false);
        } catch (e) {
            showNotification({
                title: 'Create Failed',
                message: `Could not create ${data.connection_name}. Failed: ${e}`,
                icon: <IconX size={16} />, color: 'red'
            });
        }
    };

    return (
        <>
        <Menu
            transitionProps={{ transition: "pop-top-right" }}
            position="top-end"
            width={220}
            withinPortal
            radius="md"
        >
            <Menu.Target>
            <Button
                rightSection={<IconChevronDown size={18} stroke={1.5} />}
                pr={12}
                radius="md"
            >
                Create new
            </Button>
            </Menu.Target>
            <Menu.Dropdown>
            {INTEGRATIONS.map(({ key, label, icon, shortcut }) => (
                <Menu.Item
                key={key}
                leftSection={icon(theme)}
                rightSection={
                    <Text size="xs" tt="uppercase" fw={700} c="dimmed">
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
            size="lg"
        >
            <IntegrationForm
            service_type={selectedIntegration}
            onSubmit={handleFormSubmit}
            />
        </Modal>
        </>
    );
    };
