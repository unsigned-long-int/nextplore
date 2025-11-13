import { useMemo, useState } from 'react';
import {
    ActionIcon,
    Badge,
    Button,
    Combobox,
    Group,
    ScrollArea,
    Stack,
    Text,
    TextInput, Tooltip,
    useCombobox
} from '@mantine/core';
import {IconCertificate, IconDownload, IconPlus} from '@tabler/icons-react';
import { useCertProfiles } from '@/features/cert/hooks/useCertProfiles';

const stateColor: Record<string, string> = {
    ACTIVE: 'green',
    ASSIGNED: 'blue',
    PENDING: 'yellow',
    REVOKED: 'red',
    EXPIRED: 'gray',
};

type Props = {
    value: string | null;
    onChange: (kid: string | null, name: string | null) => void;
    onCreateRequested: () => void;
};

function normalizePem(pem: string): string {
    return pem.replace(/\r\n?/g, '\n').trimEnd() + '\n';
}

function downloadPem(pem: string, filename: string): void {
    const blob = new Blob([normalizePem(pem)], { type: 'application/x-pem-file'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = makeSafeFileName(filename);
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

function makeSafeFileName(s: string, fallback = 'certificate.pem'): string {
  const cleaned = s.replace(/[^A-Za-z0-9._-]/g, '');
  return cleaned || fallback;
}


export const CertPicker = ({ value, onChange, onCreateRequested }: Props) => {
    const { data, isLoading, isError, refetch } = useCertProfiles();
    const [input, setInput] = useState(value ?? '');

    const list = data ?? [];
    const filtered = useMemo(() => {
        const q = (input ?? '').toLowerCase().trim();
        if (!q) return list;
        return list.filter(
            (c) => {
                const kid = (c?.cert_kid ?? '').toString().toLowerCase();
                const st = (c?.state ?? '').toString().toLowerCase();
                return kid.includes(q) || st.includes(q);
            }
        );
    }, [input, list]);

    const combobox = useCombobox({
        scrollBehavior: 'smooth',
        onDropdownClose: () => combobox.resetSelectedOption(),
    });

    const handleSubmitOption = (optionValue: string) => {
        const cert = list.find((c) => c.id === optionValue);
        if (cert) {
            setInput(cert.cert_kid);
            onChange(cert.cert_kid, cert.cert_name);
        }
        combobox.closeDropdown();
    };


    const options = filtered.map((c) => {
        const kid = (c?.cert_kid ?? '').toString();
        const st = (c?.state ?? '').toString();
        return (
            <Combobox.Option value={c.id} key={c.id}>
                <Group justify='space-between' wrap='nowrap'>
                    <Group gap='xs' wrap='nowrap'>
                        <IconCertificate size={16}/>
                          <Text
                            ff='monospace'
                            truncate
                            maw={200}
                            title={kid}
                          >
                              {kid}
                          </Text>
                    </Group>
                    <Badge size='sm' variant='light' color={stateColor[st] ?? 'gray'}>
                        {st}
                    </Badge>
                    <Tooltip label='Download PEM'>
                        <ActionIcon
                            variant='subtle'
                            aria-label='Download PEM'
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={(e) => {
                                e.stopPropagation();
                                downloadPem(c.public_cert_pem, `${c.id}.pem`);
                            }}
                        >
                            <IconDownload size={16} />
                        </ActionIcon>
                    </Tooltip>
                </Group>
            </Combobox.Option>
        );
    });

    if (isLoading) return <Text size='sm'>Loading certificates…</Text>;
    if (isError) {
        return (
            <Group gap='sm'>
                <Text c='red'>Failed to load certificates.</Text>
                <Button variant='outline' size='xs' onClick={() => refetch()}>
                    Retry
                </Button>
            </Group>
        );
    }

    return (
        <Stack gap='xs'>
            <Combobox onOptionSubmit={handleSubmitOption} store={combobox} withinPortal={false}>
                <Combobox.Target>
                    <TextInput
                        label='Azure Certificate (KID)'
                        placeholder='Search by KID or state'
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
                        <ScrollArea.Autosize mah={220} type='scroll'>
                            {options.length === 0 ? (
                                <Combobox.Empty>Nothing found</Combobox.Empty>
                            ): (options)}
                        </ScrollArea.Autosize>
                    </Combobox.Options>
                </Combobox.Dropdown>
            </Combobox>

            <Group>
                <Button
                    type='button'
                    onClick={() => onCreateRequested()}
                    leftSection={<IconPlus size={16} />}
                >
                    Create certificate
                </Button>
                {value && (
                    <Button
                        type='button'
                        variant='light'
                        onClick={() => { setInput(''); onChange(null, null);}}>
                        Clear
                    </Button>
                )}
            </Group>
        </Stack>
    );
};