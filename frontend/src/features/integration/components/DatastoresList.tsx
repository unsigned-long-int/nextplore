import { Text } from '@mantine/core';
import { useState } from 'react';
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';

import { DatastoreTable } from '@/features/integration/components/DatastoreTable.tsx';
import { useDatastoreProfiles } from '@/features/integration/hooks/useDatastoreProfiles.ts';
import { useUpdateDatastore } from '@/features/integration/hooks/useUpdateDatastore.ts';
import { useDeleteDatastore } from '@/features/integration/hooks/useDeleteDatastore.ts';
import { LoadingOverlay } from '@/shared/components/LoadingOverlay';



export const DatastoresList = () => {
    const updateDatastore = useUpdateDatastore();
    const deleteDatastore = useDeleteDatastore();

    const { isLoading, isError, data = [] } = useDatastoreProfiles();
    const [selection, setSelection] = useState<string[]>([]);

    const toggleAutosync = async (index: number, enabled: boolean) => {
        const row = data[index];
        if (!row) return;

        try {
            await updateDatastore.mutateAsync({
                id: row.id,
                data: {autosync_on: enabled}
            });
            row.autosync_on = enabled;
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
        const confirmed = window.confirm('Are you sure you want to delete this data_store?');
        if (!confirmed) return;
        try {
            await deleteDatastore.mutateAsync(id);
             showNotification({
                title: 'Data store Deleted',
                message: `Data store ${id} deleted.`,
                icon: <IconCheck size={16} />, color: 'green'
            });
        } catch (e) {
            showNotification({
                title: 'Delete Failed',
                message: `Could not delete data store. Failed: ${e}`,
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

    if (isLoading) return <LoadingOverlay loadingText='Loading data stores...'/>;
    if (isError) return <Text c='red'>Failed to load data stores</Text>;
    if (!data.length) return <Text>No data stores data available.</Text>;

    return (
        <DatastoreTable
            datastores={data}
            selection={selection}
            toggleRow={toggleRow}
            toggleAll={toggleAll}
            onToggleAutosync={toggleAutosync}
            onDelete={removeIntegration}
        />
    );
};
