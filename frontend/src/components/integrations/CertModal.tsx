import { Modal, Button, Group, NumberInput, Select, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import type { CertCreateRequest } from '../../interface/integration/cert-create-request.interface';

type Props = {
  opened: boolean;
  loading?: boolean;
  onClose: () => void;
  onSubmit: (data: CertCreateRequest) => Promise<void> | void;
};

const PURPOSE_OPTIONS = [
  { value: 'SIGNING', label: 'Signing' },
  { value: 'ENCRYPTION', label: 'Encryption' },
  { value: 'MUTUAL_TLS', label: 'Mutual TLS' },
];

export function CertModal({ opened, loading, onClose, onSubmit }: Props) {
  const form = useForm<{
    purpose: string | null;
    key_size: number | null;
    validity_in_months: number | null;
  }>({
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
    <Modal opened={opened} onClose={onClose} title="Create certificate" centered>
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap="md">
          <Select
            label="Purpose"
            placeholder="(optional)"
            data={PURPOSE_OPTIONS}
            clearable
            {...form.getInputProps('purpose')}
          />

          <NumberInput
            label="Key size"
            placeholder="(optional, e.g. 2048)"
            allowNegative={false}
            allowDecimal={false}
            min={0}
              value={form.values.key_size ?? undefined}
                onChange={(v) => form.setFieldValue('key_size', v === '' ? null : Number(v))}
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

          <Group justify="flex-end" mt="sm">
            <Button variant="default" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              Create
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
