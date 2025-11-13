import { Text } from '@mantine/core';
import { useState } from 'react';
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';

import { IntegrationTable } from '@/features/integration/components/IntegrationTable';
import { useIntegrationProfiles } from '@/features/integration/hooks/useIntegrationProfiles';
import { useUpdateIntegration } from '@/features/integration/hooks/useUpdateIntegration';
import { useDeleteIntegration } from '@/features/integration/hooks/useDeleteIntegration';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';



export const IntegrationsList = () => {
    const updateIntegration = useUpdateIntegration();
    const deleteIntegration = useDeleteIntegration();

    const { isLoading, isError, data = [] } = useIntegrationProfiles();
    const [selection, setSelection] = useState<string[]>([]);

    const toggleAutosync = async (index: number, enabled: boolean) => {
        const row = data[index];
        if (!row) return;

        try {
            await updateIntegration.mutateAsync({
                id: row.id,
                data: {autosync_on: enabled}
            });
            showNotification({
                title: 'Integration Updated',
                message: `${row.connection_name} autosync ${enabled ? 'enabled' : 'disabled'}`,
                icon: <IconCheck size={16}/>, color: 'green'
            });
        } catch (e) {
            showNotification({
                title: 'Update Failed',
                message: `Could not update ${row.connection_name}`,
                icon: <IconX size={16}/>, color: 'red'
            });
        }
    };

    const removeIntegration = async (id: string) => {
        const confirmed = window.confirm('Are you sure you want to delete this integration?');
        if (!confirmed) return;
        try {
            await deleteIntegration.mutateAsync(id);
             showNotification({
                title: 'Integration Deleted',
                message: `Integration ${id} deleted.`,
                icon: <IconCheck size={16} />, color: 'green'
            });
        } catch (e) {
            showNotification({
                title: 'Delete Failed',
                message: `Could not delete integration. Failed: ${e}`,
                icon: <IconX size={16}/>, color: 'red'
            });
        }
    };

    const toggleRow = (id: string) => {
        setSelection((current) =>
        current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
        );
    };

    const toggleAll = () => {
        setSelection((current) =>
                current.length === data.length ? [] : data.map((i) => i.id)
            );
        };

    if (isLoading) return <LoadingOverlay loadingText='Loading integrations...'/>;
    if (isError) return <Text c='red'>Failed to load integrations</Text>;
    if (!data.length) return <Text>No integrations data available.</Text>;

    return (
        <IntegrationTable
            integrations={data}
            selection={selection}
            toggleRow={toggleRow}
            toggleAll={toggleAll}
            onToggleAutosync={toggleAutosync}
            onDelete={removeIntegration}
        />
    );
};
