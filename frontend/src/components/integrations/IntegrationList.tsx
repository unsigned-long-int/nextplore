import { Text } from '@mantine/core';
import { useState } from 'react';
import { useIntegrationsData } from '../../hooks/useIntegrationsData';
import { LoadingOverlay } from '../loading_overlay/LoadingOverlay';
import { IntegrationTable } from './IntegrationTable';


export const IntegrationsList = () => {
    const { integrations, loading, error, toggleAutosync, removeIntegration } = useIntegrationsData();
    const [selection, setSelection] = useState<string[]>([]);

    const toggleRow = (id: string) => {
        setSelection((current) =>
        current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
        );
    };

    const toggleAll = () => {
            setSelection((current) =>
                current.length === integrations.length ? [] : integrations.map((i) => i.id)
            );
        };

    if (loading) return <LoadingOverlay loadingText="Loading integrations..."/>;
    if (error) return <Text c="red">{error}</Text>;
    if (!integrations.length) return <Text>No integrations data available.</Text>;

    return (
        <IntegrationTable
            integrations={integrations}
            selection={selection}
            toggleRow={toggleRow}
            toggleAll={toggleAll}
            onToggleAutosync={toggleAutosync}
            onDelete={removeIntegration}
        />
    );
};
