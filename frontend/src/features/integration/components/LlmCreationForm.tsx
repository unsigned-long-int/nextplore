import { Button, Modal } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconPlus, IconX } from '@tabler/icons-react';
import { useState } from 'react';
import { useCreateLlm } from '@/features/integration/hooks/useCreateLlm.ts';
import { LlmForm } from '@/features/integration/components/LlmForm.tsx';
import type { LlmModelCreateRequest } from '@/shared/api/services/integration/types.gen.ts';
import {useTestLlm} from "@/features/ai-query/hooks/useTestLlm.ts";

export const LlmCreationForm = () => {
    const createLlm = useCreateLlm();
    const testLlm = useTestLlm();
    const [modalOpened, setModalOpened] = useState(false);

    const handleTest = async (data: LlmModelCreateRequest) => {
        try {
            await testLlm.mutateAsync(data);
            showNotification({
                title: 'Connection successful',
                message: `${data.label} is reachable and responding.`,
                icon: <IconCheck size={16} />,
                color: 'teal',
            });
        } catch (e: any) {
            showNotification({
                title: 'Connection failed',
                message: e?.message ?? `Could not reach ${data.label}`,
                icon: <IconX size={16} />,
                color: 'red',
            });
        }
    };

    const handleFormSubmit = async (data: LlmModelCreateRequest) => {
        try {
            await createLlm.mutateAsync(data);
            showNotification({
                title: 'LLM Model Added',
                message: `${data.label} was successfully connected`,
                icon: <IconCheck size={16} />,
                color: 'green',
            });
            setModalOpened(false);
        } catch (e: any) {
            showNotification({
                title: 'Create Failed',
                message: `Could not add ${data.label}. Failed: ${e?.message ?? e}`,
                icon: <IconX size={16} />,
                color: 'red',
            });
        }
    };


    return (
        <>
            <Button
                leftSection={<IconPlus size={16} stroke={1.5} />}
                radius='md'
                color='violet'
                onClick={() => setModalOpened(true)}
            >
                Add LLM Model
            </Button>

            <Modal
                opened={modalOpened}
                onClose={() => setModalOpened(false)}
                title='Connect Language Model'
                size='lg'
            >
                <LlmForm
                    onSubmit={handleFormSubmit}
                    onTest={handleTest}
                    loading={createLlm.isPending}
                    testing={testLlm.isPending}
                />
            </Modal>
        </>
    );
};