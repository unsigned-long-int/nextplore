import {
    Box,
    Button,
    Group,
    NumberInput,
    PasswordInput,
    Select,
    Switch,
    TextInput,
    Textarea,
    Title,
    Divider,
    Text,
    Stack,
    Paper,
    Badge,
    ActionIcon,
    Tooltip,
    Loader,
    ThemeIcon,
    Collapse
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';
import {
    IconCheck,
    IconX,
    IconSparkles,
    IconRefresh,
    IconDatabase,
    IconShield,
    IconNetwork,
    IconKey,
    IconInfoCircle,
    IconChevronDown,
    IconChevronUp,
    IconPlugConnected,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useTestIntegration } from '@/features/integration/hooks/useTestIntegration';
import { useGetDescriptionEnhancement } from "@/features/ai-query/hooks/useGetDescriptionEnhancement.ts";
import { CloudProviderPicker, type CloudProvider } from '@/features/integration/components/CloudProviderPicker';
import { CertPicker } from '@/features/cert/components/CertPicker';
import { Auth, DB, Cloud, type IntegrationCreateRequest } from '@/shared/api/services/integration/types.gen';
import { useCreateCert } from '@/features/cert/hooks/useCreateCert';
import { CertModal } from '@/features/cert/components/CertModal';

const AUTH_OPTIONS: { value: Auth; label: string }[] = [
    { value: Auth.IAM, label: 'IAM' },
    { value: Auth.SECRET, label: 'Secret' },
    { value: Auth.CERT, label: 'Certificate' },
    { value: Auth.PASSWORD_NATIVE, label: 'Password (native)' },
    { value: Auth.PASSWORD_PROXY, label: 'Password (proxy)' },
    { value: Auth.JWT, label: 'JWT' },
];

const isRdms = (db?: DB | string | null) =>
    db === DB.POSTGRESQL || db === DB.SQLSERVER || db === DB.MYSQL;

const DB_DEFAULTS: Record<string, number> = {
    [DB.POSTGRESQL]: 5432,
    [DB.MYSQL]: 3306,
    [DB.SQLSERVER]: 1433,
    [DB.SNOWFLAKE]: 443,
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

type Props = {
    service_type: DB;
    onSubmit: (values: IntegrationCreateRequest) => void;
};

export const IntegrationForm: React.FC<Props> = ({ service_type, onSubmit }) => {
    const [certOpen, setCertOpen] = useState(false);
    const [certRefreshKey, setCertRefreshKey] = useState(0);
    const [enhancing, setEnhancing] = useState(false);
    const createCert = useCreateCert();
    const dbEnum = service_type as DB;
    const testIntegration = useTestIntegration();
    const getDescriptionEnhancement = useGetDescriptionEnhancement();

    const form = useForm<IntegrationCreateRequest>({
        initialValues: {
            auth: Auth.PASSWORD_NATIVE,
            cloud: isRdms(dbEnum) ? Cloud.AWS : Cloud.SNOWFLAKE_MANAGED,
            db: dbEnum,
            connection_name: '',
            host: '',
            database_name: '',
            descr: '',
            warehouse: null,
            tenant_id: null,
            client_id: null,
            region: null,
            port: isRdms(dbEnum) ? 5432 : null,
            kek_kid: null,
            azure_cert_kid: null,
            azure_cert_name: null,
            azure_public_key_pem: null,
            snowflake_public_key_pem: null,
            username: '',
            password: '',
            client_secret: null,
            aws_role_arn: null,
            aws_external_id: null,
            autosync_on: true,
        },
        transformValues: (values) => ({
            ...values,
            host: values.host?.trim(),
            database_name: values.database_name?.trim(),
            username: values.username?.trim() || null,
            password: values.password?.trim() || null,
            client_secret: values.client_secret?.trim() || null,
            warehouse: values.warehouse?.trim() || null,
            tenant_id: values.tenant_id?.trim() || null,
            client_id: values.client_id?.trim() || null,
            region: values.region?.trim() || null,
            azure_cert_kid: values.azure_cert_kid?.trim() || null,
            azure_cert_name: values.azure_cert_name?.trim() || null,
            azure_public_key_pem: values.azure_public_key_pem?.trim() || null,
            snowflake_public_key_pem: values.snowflake_public_key_pem?.trim() || null,
            aws_role_arn: values.aws_role_arn?.trim() || null,
            aws_external_id: values.aws_external_id?.trim() || null,
        }),
    });

    useEffect(() => {
        if (!isRdms(dbEnum)) return;
        form.setFieldValue('port', DB_DEFAULTS[dbEnum] ?? 5432);
    }, [dbEnum]);

    const handleSubmit = (values: IntegrationCreateRequest) => {
        onSubmit(form.getTransformedValues(values));
    };

    const handleTest = async (value: IntegrationCreateRequest) => {
        const payload = form.getTransformedValues(value);
        try {
            const result = await testIntegration.mutateAsync(payload);
            if (!result?.success) throw new Error('Unhandled Error');
            showNotification({
                title: 'Connection successful',
                message: `${value.connection_name} is reachable.`,
                icon: <IconCheck size={16} />,
                color: 'teal',
            });
        } catch (e) {
            showNotification({
                title: 'Connection failed',
                message: `${value.connection_name} — ${e}`,
                icon: <IconX size={16} />,
                color: 'red',
            });
        }
    };

    const handleEnhanceDescription = async () => {
        const name = form.values.connection_name?.trim();
        const raw = form.values.descr?.trim();

        if (!name) {
            showNotification({
                title: 'Connection name required',
                message: 'Enter a connection name before enhancing the description.',
                color: 'orange',
            });
            return;
        }

        setEnhancing(true);
        const payload = {
            prompt: `You are helping create a vector-search-friendly description for a database integration
                    Integration name: "${name}"
                    Database type: "${dbEnum}"
                    User's raw description: "${raw || '(none provided)'}"
                    
                    Write a concise 2-3 sentence description that:
                    - Clearly states what domain/industry this database covers
                    - Lists the key entities, concepts, or data types likely stored in it
                    - Uses specific, searchable terminology that will help an AI distinguish it from similar databases
                    - Is factual and neutral in tone
                    
                    Return ONLY the description text, no preamble, no quotes.`,
        }
        try {
            const result = await getDescriptionEnhancement.mutateAsync(payload);
            const enhanced = result.response
            if (enhanced) {
                form.setFieldValue('descr', enhanced);
                showNotification({
                    title: 'Description enhanced',
                    message: 'Review and edit before saving.',
                    icon: <IconSparkles size={16} />,
                    color: 'violet',
                });
            }
        } catch (e) {
            showNotification({
                title: 'Enhancement failed',
                message: 'Could not reach LLM model. Edit the description manually.',
                color: 'red',
            });
        } finally {
            setEnhancing(false);
        }
    };

    const showPasswordFields =
        form.values.auth === Auth.PASSWORD_NATIVE || form.values.auth === Auth.PASSWORD_PROXY;

    const showAzureSecretSqlServer =
        form.values.auth === Auth.SECRET &&
        form.values.cloud === Cloud.AZURE &&
        form.values.db === DB.SQLSERVER;

    const showAzureSecretRdms =
        form.values.auth === Auth.SECRET &&
        form.values.cloud === Cloud.AZURE &&
        (form.values.db === DB.MYSQL || form.values.db === DB.POSTGRESQL);

    const showAzureCert =
        form.values.auth === Auth.CERT &&
        form.values.cloud === Cloud.AZURE &&
        form.values.db !== DB.SNOWFLAKE;

    const showAwsIam =
        form.values.cloud === Cloud.AWS && form.values.auth === Auth.IAM;

    const showGcpIam =
        form.values.auth === Auth.IAM &&
        form.values.cloud === Cloud.GCP &&
        form.values.db === DB.MYSQL;

    return (
        <Box maw={760} mx='auto'>
            {/* Header */}
            <Group justify='space-between' align='center' mb='xl'>
                <Group gap='sm'>
                    <ThemeIcon size='lg' radius='md' variant='light' color='violet'>
                        <IconPlugConnected size={18} />
                    </ThemeIcon>
                    <div>
                        <Title order={3} style={{ lineHeight: 1.2 }}>
                            New Integration
                        </Title>
                        <Text size='xs' c='dimmed'>
                            Connect a data source to Nextplore
                        </Text>
                    </div>
                </Group>
                <Group gap='sm'>
                    <Badge variant='dot' color='teal' size='sm'>
                        {dbEnum}
                    </Badge>
                    <Tooltip label='Automatically re-crawl on schema changes' position='left'>
                        <Switch
                            label='Auto Sync'
                            onLabel='ON'
                            offLabel='OFF'
                            size='md'
                            color='violet'
                            {...form.getInputProps('autosync_on', { type: 'checkbox' })}
                        />
                    </Tooltip>
                </Group>
            </Group>

            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack gap='md'>
                    <FormSection icon={<IconDatabase size={14} />} label='Identity'>
                        <Stack gap='sm'>
                            <Group grow align='flex-start'>
                                <TextInput
                                    label='Connection Name'
                                    placeholder='e.g. Production Analytics'
                                    required
                                    {...form.getInputProps('connection_name')}
                                />
                                <TextInput
                                    label='Database Name'
                                    placeholder={dbEnum === DB.SNOWFLAKE ? 'Account / Host' : 'e.g. analytics_db'}
                                    required
                                    {...form.getInputProps('database_name')}
                                />
                            </Group>

                            <Box>
                                <Group justify='space-between' mb={4}>
                                    <Group gap={4}>
                                        <Text size='sm' fw={500}>
                                            Store Description
                                        </Text>
                                        <Text size='sm' c='red'>*</Text>
                                        <Tooltip
                                            label='Used to semantically route AI queries to the correct data source. A precise description improves query accuracy.'
                                            multiline
                                            w={260}
                                            position='right'
                                        >
                                            <ActionIcon size='xs' variant='transparent' color='dimmed'>
                                                <IconInfoCircle size={13} />
                                            </ActionIcon>
                                        </Tooltip>
                                    </Group>
                                    <Tooltip
                                        label={
                                            !form.values.connection_name?.trim()
                                                ? 'Enter a connection name first'
                                                : 'Let AI write a vector-search-optimised description'
                                        }
                                    >
                                        <Button
                                            size='xs'
                                            variant='subtle'
                                            color='violet'
                                            leftSection={
                                                enhancing ? (
                                                    <Loader size={12} color='violet' />
                                                ) : (
                                                    <IconSparkles size={13} />
                                                )
                                            }
                                            rightSection={
                                                form.values.descr ? (
                                                    <IconRefresh size={12} />
                                                ) : null
                                            }
                                            onClick={handleEnhanceDescription}
                                            loading={enhancing}
                                            disabled={!form.values.connection_name?.trim()}
                                        >
                                            {form.values.descr ? 'Regenerate' : 'Enhance with AI'}
                                        </Button>
                                    </Tooltip>
                                </Group>
                                <Textarea
                                    placeholder='Briefly describe what data this store contains - the AI will enhance it for better search accuracy.'
                                    minRows={2}
                                    autosize
                                    required
                                    {...form.getInputProps('descr')}
                                />
                                {form.values.descr && (
                                    <Text size='xs' c='dimmed' mt={4}>
                                        This description is embedded as context for AI query routing.
                                    </Text>
                                )}
                            </Box>
                        </Stack>
                    </FormSection>

                    <FormSection icon={<IconNetwork size={14} />} label='Connection'>
                        <Stack gap='sm'>
                            {isRdms(dbEnum) && (
                                <>
                                    <Text size='xs' c='dimmed' fw={600} tt='uppercase' style={{ letterSpacing: '0.05em' }}>
                                        Cloud Provider
                                    </Text>
                                    <CloudProviderPicker
                                        value={
                                            form.values.cloud === Cloud.AWS
                                                ? 'aws'
                                                : form.values.cloud === Cloud.AZURE
                                                ? 'azure'
                                                : form.values.cloud === Cloud.GCP
                                                ? 'gcp'
                                                : null
                                        }
                                        onChange={(v) => {
                                            if (!v) return;
                                            const map: Record<CloudProvider, Cloud> = {
                                                aws: Cloud.AWS,
                                                azure: Cloud.AZURE,
                                                gcp: Cloud.GCP,
                                            };
                                            form.setFieldValue('cloud', map[v]);
                                        }}
                                    />
                                    <Divider />
                                </>
                            )}
                            <Group grow align='flex-end'>
                                <TextInput
                                    label='Host'
                                    placeholder={
                                        dbEnum === DB.SNOWFLAKE
                                            ? 'account.snowflakecomputing.com'
                                            : 'e.g. 127.0.0.1 or db.internal'
                                    }
                                    required
                                    {...form.getInputProps('host')}
                                />
                                {isRdms(dbEnum) && (
                                    <NumberInput
                                        label='Port'
                                        required
                                        w={120}
                                        style={{ flexGrow: 0 }}
                                        {...form.getInputProps('port')}
                                    />
                                )}
                            </Group>

                            {dbEnum === DB.SNOWFLAKE && (
                                <Group grow>
                                    <TextInput label='Warehouse' placeholder='COMPUTE_WH' {...form.getInputProps('warehouse')} />
                                    <TextInput label='Region' placeholder='eu-west-1' {...form.getInputProps('region')} />
                                </Group>
                            )}
                        </Stack>
                    </FormSection>

                    <FormSection icon={<IconShield size={14} />} label='Authentication'>
                        <Stack gap='sm'>
                            <Select
                                label='Auth Method'
                                placeholder='Select auth method'
                                data={AUTH_OPTIONS}
                                w='50%'
                                {...form.getInputProps('auth')}
                            />

                            {showPasswordFields && (
                                <Group grow>
                                    <TextInput label='Username' placeholder='db_user' {...form.getInputProps('username')} />
                                    <PasswordInput label='Password' placeholder='••••••••' {...form.getInputProps('password')} />
                                </Group>
                            )}

                            {showAzureSecretSqlServer && (
                                <Stack gap='sm'>
                                    <PasswordInput label='Client Secret' {...form.getInputProps('client_secret')} />
                                    <Group grow>
                                        <TextInput label='Client ID' {...form.getInputProps('client_id')} />
                                        <TextInput label='Tenant ID' {...form.getInputProps('tenant_id')} />
                                    </Group>
                                </Stack>
                            )}

                            {showAzureSecretRdms && (
                                <Stack gap='sm'>
                                    <Group grow>
                                        <TextInput label='Username' {...form.getInputProps('username')} />
                                        <PasswordInput label='Client Secret' {...form.getInputProps('client_secret')} />
                                    </Group>
                                    <Group grow>
                                        <TextInput label='Client ID' {...form.getInputProps('client_id')} />
                                        <TextInput label='Tenant ID' {...form.getInputProps('tenant_id')} />
                                    </Group>
                                </Stack>
                            )}

                            {showAzureCert && (
                                <Stack gap='sm'>
                                    <TextInput label='Username' {...form.getInputProps('username')} />
                                    <Group grow>
                                        <TextInput label='Client ID' {...form.getInputProps('client_id')} />
                                        <TextInput label='Tenant ID' {...form.getInputProps('tenant_id')} />
                                    </Group>
                                    <CertPicker
                                        key={certRefreshKey}
                                        value={form.values.azure_cert_kid ?? null}
                                        onChange={(kid, name) => {
                                            form.setFieldValue('azure_cert_kid', kid ?? null);
                                            form.setFieldValue('azure_cert_name', name ?? null);
                                        }}
                                        onCreateRequested={() => setCertOpen(true)}
                                    />
                                </Stack>
                            )}

                            {showAwsIam && (
                                <Stack gap='sm'>
                                    <Group grow>
                                        <TextInput label='AWS Role ARN' {...form.getInputProps('aws_role_arn')} />
                                        <TextInput label='AWS External ID' {...form.getInputProps('aws_external_id')} />
                                    </Group>
                                    <Group grow>
                                        <TextInput label='Username' {...form.getInputProps('username')} />
                                        <TextInput label='Region' {...form.getInputProps('region')} />
                                    </Group>
                                </Stack>
                            )}

                            {showGcpIam && (
                                <TextInput label='Username' w='50%' {...form.getInputProps('username')} />
                            )}
                        </Stack>
                    </FormSection>

                    {dbEnum === DB.SNOWFLAKE && (
                        <FormSection icon={<IconKey size={14} />} label='Advanced' defaultOpen={false}>
                            <Stack gap='sm'>
                                <Group grow>
                                    <TextInput label='Client ID' {...form.getInputProps('client_id')} />
                                    <TextInput label='Tenant ID' {...form.getInputProps('tenant_id')} />
                                </Group>
                                <Textarea
                                    label='Snowflake Public Key (PEM)'
                                    placeholder='-----BEGIN PUBLIC KEY-----'
                                    minRows={3}
                                    {...form.getInputProps('snowflake_public_key_pem')}
                                />
                            </Stack>
                        </FormSection>
                    )}

                    <Group justify='flex-end' mt='sm' gap='sm'>
                        <Button
                            variant='default'
                            leftSection={<IconPlugConnected size={15} />}
                            onClick={() => handleTest(form.values)}
                            loading={testIntegration.isPending}
                        >
                            Test Connection
                        </Button>
                        <Button
                            type='submit'
                            color='violet'
                            leftSection={<IconCheck size={15} />}
                        >
                            Create Integration
                        </Button>
                    </Group>
                </Stack>
            </form>

            <CertModal
                opened={certOpen}
                loading={createCert.isPending}
                onClose={() => setCertOpen(false)}
                onSubmit={async (payload) => {
                    try {
                        await createCert.mutateAsync(payload);
                        showNotification({ title: 'Certificate created', message: 'List refreshed.' });
                        setCertOpen(false);
                        setCertRefreshKey((k) => k + 1);
                    } catch (err: any) {
                        showNotification({
                            title: 'Creation failed',
                            message: err?.message ?? 'Unknown error',
                            color: 'red',
                        });
                    }
                }}
            />
        </Box>
    );
};