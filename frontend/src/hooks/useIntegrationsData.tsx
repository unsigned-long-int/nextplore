import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';
import { useCallback, useEffect, useState } from 'react';
import type { IntegrationProfile } from '../interface/integration-profile.interface';
import { useDeleteIntegration } from './useDeleteIntegration';
import { useIntegrations } from './useIntegrations';
import { useUpdateIntegration } from './useUpdateIntegrations';

export const useIntegrationsData = () => {
    const { fetchIntegrations } = useIntegrations();
    const { updateIntegration } = useUpdateIntegration();
    const { deleteIntegration } = useDeleteIntegration();

    const [integrations, setIntegrations] = useState<IntegrationProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [hasFetchedOnce, setHasFetchedOnce] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getIntegrations = useCallback(async () => {
        try {
            const data = await fetchIntegrations();
            setIntegrations(data);
            setHasFetchedOnce(true);
        } catch (e) {
            setError('Failed to load integrations');
        } finally {
            setLoading(false);
        }
    }, [fetchIntegrations]);

    useEffect(() => {
        if (!hasFetchedOnce) {
            getIntegrations();
        }
    }, [getIntegrations]);

    const toggleAutosync = async (index: number, enabled: boolean) => {
        const original = [...integrations];
        const updated = [...integrations];
        updated[index] = { ...updated[index], autosync_on: enabled };
        setIntegrations(updated);

        try {
            const result = await updateIntegration({ id: updated[index].id, autosync_on: enabled });
            if (!result.success) throw new Error(result.message);
            showNotification({
                title: 'Integration Updated',
                message: `${updated[index].connection_name} autosync ${enabled ? 'enabled' : 'disabled'}`,
                icon: <IconCheck size={16} />, color: 'green'
            });
        } catch (e) {
            setIntegrations(original);
            showNotification({
                title: 'Update Failed',
                message: `Could not update ${original[index].connection_name}`,
                icon: <IconX size={16} />, color: 'red'
            });
        }
    };

    const removeIntegration = async (id: string) => {
        const confirmed = window.confirm('Are you sure you want to delete this integration?');
        if (!confirmed) return;

        try {
            await deleteIntegration({ id });
            setIntegrations(prev => prev.filter(i => i.id !== id));
            showNotification({
                title: 'Integration Deleted',
                message: `Integration ${id} deleted.`,
                icon: <IconCheck size={16} />, color: 'green'
            });
        } catch (e) {
            showNotification({
                title: 'Delete Failed',
                message: `Could not delete integration. Failed: ${e}`,
                icon: <IconX size={16} />, color: 'red'
        });
        }
    };

    return { integrations, loading, error, toggleAutosync, removeIntegration };
};