import { Modal, Button, Group, NumberInput, TextInput, Select, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import type { CertCreateRequest } from '@/shared/api/services/cert/types.gen';

type Props = {
    opened: boolean;
    loading?: boolean;
    onClose: () => void;
    onSubmit: (data: CertCreateRequest) => Promise<void> | void;
};

export const CertModal = ({ opened, loading, onClose, onSubmit }: Props) => {
    const form = useForm<CertCreateRequest>({
        initialValues: {
            purpose: null,
            key_size: null,
            validity_in_months: null,
        },
        transformValues: (v) => ({
            purpose: v.purpose ?? null,
            key_size: v.key_size ?? null,
            validity_in_months: v.validity_in_months ?? null,
        }),
    });

    const handleSubmit = async (vals: typeof form.values) => {
        await onSubmit(form.getTransformedValues(vals));
        form.reset();
        onClose();
    };

    return (
        <Modal opened={opened} onClose={onClose} title='Create certificate' centered>
            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack gap='md'>
                    <TextInput
                        label='Purpose'
                        placeholder='(optional, default: "general")'
                        maxLength={20}
                        value={form.values.purpose ?? ''}
                        onChange={(e) => {
                            const raw = e.currentTarget.value;
                            const cleaned = raw
                            .toLowerCase()
                            .replace(/\s+/g, '');
                            form.setFieldValue('purpose', cleaned.slice(0, 20));
                        }}
                    />
                    <Select
                        label='Key size'
                        placeholder='Select key size (optional, default: 3072)'
                        data={[
                            { value: '2048', label: '2048' },
                            { value: '3072', label: '3072' },
                            { value: '4096', label: '4096' },
                        ]}
                        value={form.values.key_size ? String(form.values.key_size) : null}
                        onChange={(v) => form.setFieldValue('key_size', v ? Number(v) : null)}
                        clearable
                    />
                    <NumberInput
                        label="Validity (months)"
                        placeholder="(optional)"
                        allowNegative={false}
                        allowDecimal={false}
                        min={0}
                        value={form.values.validity_in_months ?? undefined}
                        onChange={(v) =>
                            form.setFieldValue('validity_in_months', v === '' ? null : Number(v))
                        }
                    />
                    <Group justify='flex-end' mt='sm'>
                        <Button variant='default' onClick={onClose}>
                            Cancel
                        </Button>
                        <Button type='submit' loading={loading}>
                            Create
                        </Button>
                    </Group>
                </Stack>
            </form>
        </Modal>
    );
};