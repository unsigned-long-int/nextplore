import {
    Box,
    Button,
    Group,
    NumberInput,
    PasswordInput,
    Select,
    Stack,
    Text,
    TextInput,
    Title,
    ThemeIcon,
    Paper,
    Collapse,
    ActionIcon,
    Loader,
    Table,
    Tooltip,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import {
    IconCheck,
    IconChevronDown,
    IconChevronUp,
    IconBrain,
    IconSettings,
    IconNetwork,
    IconSparkles,
    IconPlus,
    IconTrash,
    IconEye,
    IconEyeOff, IconPlugConnected,
} from '@tabler/icons-react';
import { useState } from 'react';
import type { LlmModelCreateRequest } from '@/shared/api/services/integration/types.gen.ts';
import { LlmProviderIcon, getLlmProviderColor } from '@/features/integration/components/LlmProviderIcon.tsx';


type ConnParam = {
    key: string;
    value: string;
    sensitive: boolean;
};


type SectionProps = {
    icon: React.ReactNode;
    label: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
};

const FormSection: React.FC<SectionProps> = ({ icon, label, children, defaultOpen = true }) => {
    const [open, setOpen] = useState(defaultOpen);
    return (
        <Paper
            withBorder
            radius='md'
            p={0}
            style={{
                borderColor: 'var(--mantine-color-dark-4)',
                overflow: 'hidden',
                background: 'var(--mantine-color-dark-8)',
            }}
        >
            <Group
                px='md'
                py='sm'
                justify='space-between'
                style={{
                    cursor: 'pointer',
                    background: 'var(--mantine-color-dark-7)',
                    borderBottom: open ? '1px solid var(--mantine-color-dark-4)' : 'none',
                    userSelect: 'none',
                }}
                onClick={() => setOpen((o) => !o)}
            >
                <Group gap='xs'>
                    <ThemeIcon size='sm' variant='transparent' color='violet'>
                        {icon}
                    </ThemeIcon>
                    <Text size='sm' fw={600} c='dimmed' tt='uppercase' style={{ letterSpacing: '0.06em' }}>
                        {label}
                    </Text>
                </Group>
                <ActionIcon size='xs' variant='transparent' color='dimmed'>
                    {open ? <IconChevronUp size={14} /> : <IconChevronDown size={14} />}
                </ActionIcon>
            </Group>
            <Collapse in={open}>
                <Box p='md'>{children}</Box>
            </Collapse>
        </Paper>
    );
};

const ConnParamsTable: React.FC<{
    params: ConnParam[];
    onChange: (params: ConnParam[]) => void;
}> = ({ params, onChange }) => {
    const update = (index: number, field: keyof ConnParam, value: string | boolean) => {
        onChange(params.map((p, i) => (i === index ? { ...p, [field]: value } : p)));
    };

    const remove = (index: number) => onChange(params.filter((_, i) => i !== index));

    const add = () => onChange([...params, { key: '', value: '', sensitive: false }]);

    return (
        <Stack gap='xs'>
            {params.length > 0 && (
                <Table verticalSpacing={6} style={{ tableLayout: 'fixed' }}>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th w='35%'>
                                <Text size='xs' c='dimmed' tt='uppercase' style={{ letterSpacing: '0.05em' }}>
                                    Key
                                </Text>
                            </Table.Th>
                            <Table.Th>
                                <Text size='xs' c='dimmed' tt='uppercase' style={{ letterSpacing: '0.05em' }}>
                                    Value
                                </Text>
                            </Table.Th>
                            <Table.Th w={64}>
                                <Tooltip label='Toggle to hide value as a secret' withArrow position='top'>
                                    <Text
                                        size='xs'
                                        c='dimmed'
                                        tt='uppercase'
                                        ta='center'
                                        style={{ letterSpacing: '0.05em', cursor: 'help' }}
                                    >
                                        Secret
                                    </Text>
                                </Tooltip>
                            </Table.Th>
                            <Table.Th w={36} />
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                        {params.map((param, i) => (
                            <Table.Tr key={i}>
                                <Table.Td>
                                    <TextInput
                                        size='xs'
                                        placeholder='e.g. api_key'
                                        value={param.key}
                                        onChange={(e) => update(i, 'key', e.currentTarget.value)}
                                        styles={{
                                            input: {
                                                fontFamily: 'var(--mantine-font-family-monospace)',
                                                fontSize: 12,
                                            },
                                        }}
                                    />
                                </Table.Td>

                                <Table.Td>
                                    {param.sensitive ? (
                                        <PasswordInput
                                            size='xs'
                                            placeholder='••••••••'
                                            value={param.value}
                                            onChange={(e) => update(i, 'value', e.currentTarget.value)}
                                        />
                                    ) : (
                                        <TextInput
                                            size='xs'
                                            placeholder='value'
                                            value={param.value}
                                            onChange={(e) => update(i, 'value', e.currentTarget.value)}
                                        />
                                    )}
                                </Table.Td>

                                <Table.Td>
                                    <Group justify='center'>
                                        <Tooltip
                                            label={param.sensitive ? 'Sensitive - click to make plain' : 'Mark as sensitive'}
                                            withArrow
                                            position='top'
                                        >
                                            <ActionIcon
                                                size='sm'
                                                variant={param.sensitive ? 'light' : 'subtle'}
                                                color={param.sensitive ? 'violet' : 'gray'}
                                                onClick={() => update(i, 'sensitive', !param.sensitive)}
                                            >
                                                {param.sensitive
                                                    ? <IconEyeOff size={13} />
                                                    : <IconEye size={13} />
                                                }
                                            </ActionIcon>
                                        </Tooltip>
                                    </Group>
                                </Table.Td>

                                <Table.Td>
                                    <ActionIcon
                                        size='sm'
                                        variant='subtle'
                                        color='red'
                                        onClick={() => remove(i)}
                                    >
                                        <IconTrash size={13} />
                                    </ActionIcon>
                                </Table.Td>
                            </Table.Tr>
                        ))}
                    </Table.Tbody>
                </Table>
            )}

            <Button
                size='xs'
                variant='subtle'
                color='violet'
                leftSection={<IconPlus size={13} />}
                onClick={add}
                style={{ alignSelf: 'flex-start' }}
            >
                Add parameter
            </Button>

            {params.length === 0 && (
                <Text size='xs' c='dimmed' mt={4}>
                    No parameters yet. Most providers require at least an <code>api_key</code>.
                </Text>
            )}
        </Stack>
    );
};

const PROVIDER_PRESETS: Record<string, {
    apiBase: string;
    placeholder?: string;
    defaultParams: ConnParam[];
}> = {
    openai:      { apiBase: 'https://api.openai.com/v1',                        defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    anthropic:   { apiBase: 'https://api.anthropic.com',                        defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    gemini:      { apiBase: 'https://generativelanguage.googleapis.com/v1beta', defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    groq:        { apiBase: 'https://api.groq.com/openai/v1',                   defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    mistral:     { apiBase: 'https://api.mistral.ai/v1',                        defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    cohere:      { apiBase: 'https://api.cohere.ai/v1',                         defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    ollama:      { apiBase: 'http://localhost:11434',                            defaultParams: [] },
    huggingface: { apiBase: 'https://router.huggingface.co/v1',                 defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    deepseek:    { apiBase: 'https://api.deepseek.com/v1',                      defaultParams: [{ key: 'api_key', value: '', sensitive: true }] },
    azure: {
        apiBase: '',
        placeholder: 'https://<resource>.openai.azure.com/openai/deployments/<deployment>',
        defaultParams: [
            { key: 'api_key',     value: '',          sensitive: true  },
            { key: 'api_version', value: '2024-02-01', sensitive: false },
        ],
    },
    other: { apiBase: '', placeholder: 'https://your-endpoint/v1', defaultParams: [] },
};

const PROVIDER_OPTIONS = Object.keys(PROVIDER_PRESETS).map((k) => ({
    value: k,
    label: k.charAt(0).toUpperCase() + k.slice(1),
}));


type Props = {
    onTest: (values: LlmModelCreateRequest) => void;
    onSubmit: (values: LlmModelCreateRequest) => void;
    loading?: boolean;
    testing?: boolean;
};


export const LlmForm: React.FC<Props> = ({ onSubmit, onTest, loading = false, testing = false  }) => {
    const [provider, setProvider] = useState<string | null>(null);
    const [apiBaseDirty, setApiBaseDirty] = useState(false);
    const [connParams, setConnParams] = useState<ConnParam[]>([
        { key: 'api_key', value: '', sensitive: true },
    ]);

    const form = useForm<Omit<LlmModelCreateRequest, 'connection_params'>>({
        initialValues: {
            model_id: '',
            label: '',
            api_base: '',
            max_tokens: 4096,
        },
        transformValues: (values) => ({
            ...values,
            model_id: values.model_id.trim(),
            label: values.label.trim(),
            api_base: values.api_base.trim(),
            connection_params: Object.fromEntries(
                connParams
                    .filter((p) => p.key.trim() !== '')
                    .map((p) => [p.key.trim(), p.value])
            ),
        }),
    });

    const handleProviderChange = (value: string | null) => {
        setProvider(value);
        if (!value) return;
        const preset = PROVIDER_PRESETS[value];
        if (!apiBaseDirty) {
            form.setFieldValue('api_base', preset.apiBase);
        }
        setConnParams(preset.defaultParams.map((p) => ({ ...p })));
    };

    const getPayload = () => form.getTransformedValues(form.values) as LlmModelCreateRequest;

    const handleSubmit = (values: Omit<LlmModelCreateRequest, 'connection_params'>) => {
        onSubmit(form.getTransformedValues(values) as LlmModelCreateRequest);
    };

    const handleTest = () => {
        onTest(getPayload());
    };

    const modelId = form.values.model_id;
    const providerColor = modelId ? getLlmProviderColor(modelId) : 'var(--mantine-color-violet-5)';

    return (
        <Box maw={760} mx='auto'>
            <Group justify='space-between' align='center' mb='xl'>
                <Group gap='sm'>
                    <ThemeIcon size='lg' radius='md' variant='light' color='violet'>
                        <IconBrain size={18} />
                    </ThemeIcon>
                    <div>
                        <Title order={3} style={{ lineHeight: 1.2 }}>
                            New LLM Model
                        </Title>
                        <Text size='xs' c='dimmed'>
                            Connect your own language model to Nextplore
                        </Text>
                    </div>
                </Group>
                {modelId && (
                    <Group gap={6} align='center' style={{
                        border: `1px solid ${providerColor}`,
                        borderRadius: 'var(--mantine-radius-sm)',
                        padding: '2px 8px',
                        opacity: 0.9,
                    }}>
                        <LlmProviderIcon modelId={modelId} size={12} />
                        <Text size='xs' fw={500} style={{ color: providerColor, fontFamily: 'monospace' }}>
                            {modelId}
                        </Text>
                    </Group>
                )}
            </Group>

            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack gap='md'>

                    <FormSection icon={<IconBrain size={14} />} label='Identity'>
                        <Stack gap='sm'>
                            <Group grow align='flex-start'>
                                <Select
                                    label='Provider'
                                    placeholder='Select provider'
                                    data={PROVIDER_OPTIONS}
                                    value={provider}
                                    onChange={handleProviderChange}
                                    clearable
                                />
                                <TextInput
                                    label='Display Label'
                                    placeholder='e.g. My GPT-4o endpoint'
                                    required
                                    {...form.getInputProps('label')}
                                />
                            </Group>
                            <TextInput
                                label='Model ID'
                                placeholder='e.g. openai/gpt-4o or meta-llama/Llama-3.1-8B-Instruct'
                                required
                                leftSection={
                                    modelId
                                        ? <LlmProviderIcon modelId={modelId} size={14} />
                                        : <IconSparkles size={14} />
                                }
                                {...form.getInputProps('model_id')}
                            />
                        </Stack>
                    </FormSection>

                    <FormSection icon={<IconNetwork size={14} />} label='Connection'>
                        <Stack gap='md'>
                            <TextInput
                                label='API Base URL'
                                placeholder={
                                    provider
                                        ? PROVIDER_PRESETS[provider]?.placeholder ?? 'https://...'
                                        : 'Select a provider or enter manually'
                                }
                                required
                                {...form.getInputProps('api_base')}
                                onChange={(e) => {
                                    setApiBaseDirty(true);
                                    form.getInputProps('api_base').onChange(e);
                                }}
                            />
                            <Box>
                                <Text size='sm' fw={500} mb={8}>
                                    Connection Parameters
                                </Text>
                                <ConnParamsTable params={connParams} onChange={setConnParams} />
                            </Box>
                        </Stack>
                    </FormSection>

                    <FormSection icon={<IconSettings size={14} />} label='Parameters'>
                        <NumberInput
                            label='Max Tokens'
                            description='Maximum tokens the model can generate per response'
                            placeholder='4096'
                            min={1}
                            max={200000}
                            step={512}
                            required
                            {...form.getInputProps('max_tokens')}
                        />
                    </FormSection>
                    <Group justify='flex-end' mt='sm' gap='sm'>
                        <Button
                            variant='default'
                            leftSection={
                                testing
                                    ? <Loader size={14} />
                                    : <IconPlugConnected size={15} />
                            }
                            loading={testing}
                            disabled={!modelId || !form.values.api_base}
                            onClick={handleTest}
                        >
                            Test Connection
                        </Button>
                        <Button
                            type='submit'
                            color='violet'
                            loading={loading}
                            leftSection={loading ? <Loader size={14} color='white' /> : <IconCheck size={15} />}
                        >
                            Add LLM Model
                        </Button>
                    </Group>

                </Stack>
            </form>
        </Box>
    );
};