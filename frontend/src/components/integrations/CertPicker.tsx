// components/CertPicker.tsx
import { useMemo, useState } from 'react';
import {
  Badge,
  Button,
  Combobox,
  Group,
  ScrollArea,
  Stack,
  Text,
  TextInput,
  useCombobox,
} from '@mantine/core';
import { IconCertificate, IconPlus } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';

import type { CertCreateRequest } from '../../interface/integration/cert-create-request.interface';
import { useCertProfiles } from '../../hooks/useCertProfiles';
import { useCreateCert } from '../../hooks/useCreateCert';
import { CertModal } from './CertModal';


const stateColor: Record<string, string> = {
  ACTIVE: 'green',
  ASSIGNED: 'blue',
  PENDING: 'yellow',
  REVOKED: 'red',
  EXPIRED: 'gray',
};

type CertPickerProps = {
  value: string | null;
  onChange: (kid: string | null) => void;
  defaultCreate?: Partial<CertCreateRequest>;
};

export function CertPicker({ value, onChange, defaultCreate }: CertPickerProps) {
  const { loading, error, certs, refetch } = useCertProfiles();
  const { createCert } = useCreateCert();

  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [input, setInput] = useState(value ?? '');

  const combobox = useCombobox({
    scrollBehavior: 'smooth',
    onDropdownClose: () => combobox.resetSelectedOption(),
  });

  const filtered = useMemo(() => {
    const q = input.toLowerCase().trim();
    if (!q) return certs;
    return certs.filter(
      (c) =>
        c.cert_kid.toLowerCase().includes(q) ||
        String(c.state).toLowerCase().includes(q)
    );
  }, [input, certs]);

  const options = filtered.map((c) => (
    <Combobox.Option value={c.id} key={c.id}>
      <Group justify="space-between" wrap="nowrap">
        <Group gap="xs" wrap="nowrap">
          <IconCertificate size={16} />
          <Text ff="monospace">{c.cert_kid}</Text>
        </Group>
        <Badge size="sm" variant="light" color={stateColor[String(c.state)] ?? 'gray'}>
          {String(c.state)}
        </Badge>
      </Group>
    </Combobox.Option>
  ));

  const handleSubmitOption = (optionValue: string) => {
    const cert = certs.find((c) => c.id === optionValue);
    if (cert) {
      setInput(cert.cert_kid);
      onChange(cert.cert_kid);
    }
    combobox.closeDropdown();
  };

  const submitCreate = async (data: CertCreateRequest) => {
    setCreating(true);
    try {
      const payload: CertCreateRequest = {
        purpose:
          data.purpose ?? defaultCreate?.purpose ?? null,
        key_size:
          (data.key_size ?? defaultCreate?.key_size ?? null) as number | null,
        validity_in_months:
          (data.validity_in_months ?? defaultCreate?.validity_in_months ?? null) as number | null,
      };

      await createCert(payload);
      await refetch();
      showNotification({
        title: 'Certificate created',
        message: 'The certificate list has been refreshed.',
      });
    } catch (e: any) {
      showNotification({
        title: 'Creation failed',
        message: e?.message ?? String(e),
        color: 'red',
      });
    } finally {
      setCreating(false);
    }
  };

  // Loading / Error / Empty
  if (loading) return <Text size="sm">Loading certificates…</Text>;

  if (error) {
    return (
      <Group gap="sm">
        <Text c="red">Failed to load certificates.</Text>
        <Button variant="outline" size="xs" onClick={refetch}>
          Retry
        </Button>
      </Group>
    );
  }

  if (certs.length === 0) {
    return (
      <Stack gap="xs">
        <Text size="sm" c="dimmed">
          No certificate available — create one.
        </Text>
        <Button onClick={() => setCreateOpen(true)} leftSection={<IconPlus size={16} />}>
          Create certificate
        </Button>

        <CertModal
          opened={createOpen}
          loading={creating}
          onClose={() => setCreateOpen(false)}
          onSubmit={submitCreate}
        />
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      <Combobox onOptionSubmit={handleSubmitOption} store={combobox} withinPortal={false}>
        <Combobox.Target>
          <TextInput
            label="Azure Certificate (KID)"
            placeholder="Search by KID or state"
            value={input}
            onChange={(event) => {
              setInput(event.currentTarget.value);
              combobox.openDropdown();
              combobox.updateSelectedOptionIndex();
            }}
            onClick={() => combobox.openDropdown()}
            onFocus={() => combobox.openDropdown()}
            onBlur={() => combobox.closeDropdown()}
          />
        </Combobox.Target>

        <Combobox.Dropdown>
          <Combobox.Options>
            <ScrollArea.Autosize mah={220} type="scroll">
              {options.length === 0 ? (
                <Combobox.Empty>Nothing found</Combobox.Empty>
              ) : (
                options
              )}
            </ScrollArea.Autosize>
          </Combobox.Options>
        </Combobox.Dropdown>
      </Combobox>

      <Group>
        <Button onClick={() => setCreateOpen(true)} leftSection={<IconPlus size={16} />}>
          Create certificate
        </Button>
        {value && (
          <Button variant="light" onClick={() => { setInput(''); onChange(null); }}>
            Clear
          </Button>
        )}
      </Group>

      <CertModal
        opened={createOpen}
        loading={creating}
        onClose={() => setCreateOpen(false)}
        onSubmit={submitCreate}
      />
    </Stack>
  );
}
