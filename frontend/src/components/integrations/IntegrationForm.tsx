/*
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
    Text
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX } from "@tabler/icons-react";
import { useState, useEffect } from "react";

import { useTestIntegration } from "../../hooks/useTestIntegration";
import { Auth } from '../../interface/integration/auth.interface';
import { DB } from '../../interface/integration/db.interface';
import { Cloud } from '../../interface/integration/cloud.interface';
import { CloudProviderPicker, type CloudProvider } from "./CloudProviderPicker";
import { CertPicker } from "@/features/cert/components/CertPicker";
import type { IntegrationCreateRequest } from '../../interface/integration/integration-create-request.interface';


const AUTH_OPTIONS = [
    { value: Auth.IAM, label: "IAM" },
    { value: Auth.SECRET, label: "Secret" },
    { value: Auth.CERT, label: "Cert" },
    { value: Auth.PASSWORD_NATIVE, label: "Password (Native)" },
    { value: Auth.PASSWORD_PROXY, label: "Password (Proxy)" },
    { value: Auth.JWT, label: "JWT" },
];

const isRdbms = (db?: DB | string | null) =>
    db === DB.POSTGRESQL || db === DB.SQLSERVER || db === DB.MYSQL;

type IntegrationFormProps = {
    service_type: DB;
    onSubmit: (values: IntegrationCreateRequest) => void;
};


export const IntegrationForm: React.FC<IntegrationFormProps> =  ({
    service_type,
    onSubmit,
}) => {
    const [testing, setTesting] = useState(false);
    const { testIntegration } = useTestIntegration();
    const dbEnum = service_type as DB;

    const form = useForm<IntegrationCreateRequest>({
        initialValues: {
            auth: Auth.PASSWORD_NATIVE,
            cloud: isRdbms(dbEnum) ? Cloud.AWS : Cloud.SNOWFLAKE_MANAGED,
            db: dbEnum,
            connection_name: "",
            host: "",
            database_name: "",
            warehouse: null,
            tenant_id: null,
            client_id: null,
            region: null,
            port: isRdbms(dbEnum) ? 5432 : null,
            kek_kid: null,
            azure_cert_kid: null,
            azure_public_key_pem: null,
            snowflake_public_key_pem: null,
            username: "",
            password: "",
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
            azure_public_key_pem: values.azure_public_key_pem?.trim() || null,
            snowflake_public_key_pem: values.snowflake_public_key_pem?.trim() || null,
            aws_role_arn: values.aws_role_arn?.trim() || null,
            aws_external_id: values.aws_external_id?.trim() || null,
        }),
    });

    useEffect(() => {
        if (!isRdbms(dbEnum)) return;
        const defaults: Record<DB, number> = {
            [DB.POSTGRESQL]: 5432,
            [DB.MYSQL]: 3306,
            [DB.SQLSERVER]: 1433,
            [DB.SNOWFLAKE]: 443,
        } as const;
        form.setFieldValue("port", defaults[dbEnum] ?? 5432);
    }, [dbEnum]);

    const handleSubmit = (values: IntegrationCreateRequest) => {
        onSubmit(form.getTransformedValues(values));
    };

    const handleTest = async (values: IntegrationCreateRequest) => {
        setTesting(true);
        try {
            const result = await testIntegration(form.getTransformedValues(values));
            if (!result.success) throw new Error('Unhandled Error');
            showNotification({
                title: 'Integration Test Successful',
                message: `Connection: ${values.connection_name} was successful.`,
                icon: <IconCheck size={16} />, color: 'green'
            });
        } catch (e) {
            showNotification({
                title: 'Test Failed',
                message: `Connection: ${values.connection_name} failed with error ${e}`,
                icon: <IconX size={16} />, color: 'red'
            });
        } finally {
            setTesting(false);
        }
    };

    return (
        <Box maw={720} mx="auto">
            <Group justify="space-between" align="center" mb="md">
                <Title order={3}>Create Integration</Title>
                <Switch
                    label="Auto Sync"
                    onLabel="ON"
                    offLabel="OFF"
                    size="lg"
                    {...form.getInputProps("autosync_on", { type: "checkbox" })}
                />
            </Group>
                <form onSubmit={form.onSubmit(handleSubmit)}>
                    <Group grow mb="md">
                        <TextInput label="Service (DB)" value={dbEnum} readOnly />
                        <Select
                            label="Auth"
                            placeholder="Select auth method"
                            data={AUTH_OPTIONS}
                            {...form.getInputProps("auth")}
                        />
                    </Group>
                     {isRdbms(dbEnum) && (
                        <>
                            <Text size="sm" fw={600} mb={6}>Cloud provider</Text>
                            <CloudProviderPicker
                                value={
                                    form.values.cloud === Cloud.AWS
                                    ? "aws"
                                    : form.values.cloud === Cloud.AZURE
                                    ? "azure"
                                    : form.values.cloud === Cloud.GCP
                                    ? "gcp"
                                    : null
                                }
                            onChange={(v) => {
                            const map: Record<CloudProvider, Cloud> = {
                                aws: Cloud.AWS,
                                azure: Cloud.AZURE,
                                gcp: Cloud.GCP,
                            };
                            form.setFieldValue("cloud", map[v]);
                        }}
                    />
                    <Divider my="md" />
                </>
            )}
            <Group grow>
                <TextInput label="Connection Name" required {...form.getInputProps("connection_name")} />
                {isRdbms(dbEnum) ? (
                    <TextInput label="Host" required {...form.getInputProps("host")} />
                ) : (
                    <TextInput label="Account / Host" required {...form.getInputProps("host")} />
                )}
            </Group>
            <Group grow mt="md">
                {isRdbms(dbEnum) && (
                    <NumberInput label="Port" required {...form.getInputProps("port")} />
                )}
                <TextInput
                    label={dbEnum === DB.SNOWFLAKE ? "Database" : "Database Name"}
                    required
                    {...form.getInputProps("database_name")}
                />
            </Group>
            <Group grow mt="md">
                {(
                    form.values.auth === Auth.PASSWORD_NATIVE
                    || form.values.auth === Auth.PASSWORD_PROXY) && (
                    <>
                        <TextInput label="Username" {...form.getInputProps("username")} />
                        <PasswordInput label="Password" {...form.getInputProps("password")} />
                    </>
                )}
                {(
                    form.values.auth === Auth.SECRET
                    && form.values.cloud === Cloud.AZURE
                    && form.values.db === DB.SQLSERVER) && (
                    <>
                        <Group grow mt="md">
                            <PasswordInput label="Secret" {...form.getInputProps("client_secret")} />
                        </Group>
                        <Group grow mt="md">
                            <TextInput label="Client ID" {...form.getInputProps("client_id")} />
                            <TextInput label="Tenant ID" {...form.getInputProps("tenant_id")} />
                        </Group>
                    </>
                )}
                {(
                    form.values.auth === Auth.SECRET
                    && form.values.cloud === Cloud.AZURE
                    && (form.values.db === DB.MYSQL || form.values.db === DB.POSTGRESQL)) && (
                        <>
                            <Group grow mt="md">
                                <TextInput label="Username" {...form.getInputProps("username")} />
                                <PasswordInput label="Secret" {...form.getInputProps("client_secret")} />
                            </Group>
                            <Group grow mt="md">
                                <TextInput label="Client ID" {...form.getInputProps("client_id")} />
                                <TextInput label="Tenant ID" {...form.getInputProps("tenant_id")} />
                            </Group>
                        </>
                )}
                {(
                    form.values.auth === Auth.CERT
                    && form.values.cloud === Cloud.AZURE
                    && (form.values.db !== DB.SNOWFLAKE)) && (
                       <>
                            <Group grow mt="md">
                              <TextInput label="Username" {...form.getInputProps('username')} />
                            </Group>
                            <Group grow mt="md">
                              <TextInput label="Client ID" {...form.getInputProps('client_id')} />
                              <TextInput label="Tenant ID" {...form.getInputProps('tenant_id')} />
                            </Group>
                           <Group grow mt='md'>
                               <CertPicker
                                  value={form.values.azure_cert_kid ?? null}
                                  onChange={(kid) => form.setFieldValue('azure_cert_kid', kid ?? null)}
                                  defaultCreate={{ purpose: null, key_size: null, validity_in_months: null }}
                              />
                           </Group>
                    </>
                )}

            </Group>
            {dbEnum === DB.SNOWFLAKE && (
                <>
                    <Group grow mt="md">
                        <TextInput label="Warehouse" {...form.getInputProps("warehouse")} />
                        <TextInput label="Region" {...form.getInputProps("region")} />
                    </Group>
                    <Group grow mt="md">
                        <TextInput label="Client ID" {...form.getInputProps("client_id")} />
                        <TextInput label="Tenant ID" {...form.getInputProps("tenant_id")} />
                    </Group>
                    <Group grow mt="md">
                        <Textarea label="Snowflake Public Key (PEM)" minRows={3} {...form.getInputProps("snowflake_public_key_pem")} />
                    </Group>
                </>
            )}
            {(
                form.values.cloud === Cloud.AWS
                && form.values.auth === Auth.IAM) && (
                <Group grow mt="md">
                    <TextInput label="AWS Role ARN" {...form.getInputProps("aws_role_arn")} />
                    <TextInput label="AWS External ID" {...form.getInputProps("aws_external_id")} />
                </Group>
            )}
            <Group justify="flex-end" mt="lg">
                <Button variant="default" onClick={() => handleTest(form.values)} loading={testing}>
                    Test Integration
                </Button>
                <Button type="submit">Create Integration</Button>
            </Group>
        </form>
    </Box>
    );
};
*/