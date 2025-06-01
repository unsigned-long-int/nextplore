import {
  TextInput,
  PasswordInput,
  Textarea,
  NumberInput,
  Select,
  Button,
  Group,
  Box,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';

export interface Integration {
  organization_id: string;
  created_by: string;
  type: string;
  method: string;
  name: string;
  host?: string | null;
  port?: number | null;
  database?: string | null;
  username?: string | null;
  password_encrypted?: string | null;
  api_key_encrypted?: string | null;
  kerberos_principal?: string | null;
  kerberos_keytab_encrypted?: string | null;
  connection_uri?: string | null;
  extra?: Record<string, any> | null;
  created_at?: string;
  updated_at?: string;
};

interface IntegrationFormProps {
  organization_id: string,
  created_by: string,
  type: string,
  onSubmit: (data: Integration) => void;
}

export const IntegrationForm = ({organization_id, created_by, type, onSubmit }: IntegrationFormProps) => {
  const form = useForm({
    initialValues: {
      method: '',
      name: '',
      host: '',
      port: undefined,
      database: '',
      username: '',
      password: '',
      api_key: '',
      kerberos_principal: '',
      kerberos_keytab: '',
      connection_uri: '',
      extra: '',
    },
  });

  const handleSubmit = (values: typeof form.values) => {
    const payload = {
      organization_id: organization_id,
      created_by: created_by,
      type: type,
      method: values.method,
      name: values.name,
      host: values.host,
      port: values.port,
      database: values.database,
      username: values.username,
      password_encrypted: values.password ? btoa(values.password) : null,
      api_key_encrypted: values.api_key ? btoa(values.api_key) : null,
      kerberos_principal: values.kerberos_principal || null,
      kerberos_keytab_encrypted: values.kerberos_keytab ? btoa(values.kerberos_keytab) : null,
      connection_uri: values.connection_uri || null,
      extra: values.extra ? JSON.parse(values.extra) : null
    };

    onSubmit(payload);
  };

  return (
    <Box maw={600} mx="auto">
      <Title order={3} mb="md">Create Integration</Title>

      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Select
          label="Method"
          placeholder="e.g. direct, ODBC, JDBC"
          data={['direct', 'odbc', 'jdbc', 'kerberos']}
          {...form.getInputProps('method')}
        />

        <TextInput label="Name" {...form.getInputProps('name')} />
        <TextInput label="Host" {...form.getInputProps('host')} />
        <NumberInput label="Port" {...form.getInputProps('port')} />
        <TextInput label="Database" {...form.getInputProps('database')} />
        <TextInput label="Username" {...form.getInputProps('username')} />
        <PasswordInput label="Password" {...form.getInputProps('password')} />
        <PasswordInput label="API Key" {...form.getInputProps('api_key')} />
        <TextInput label="Kerberos Principal" {...form.getInputProps('kerberos_principal')} />
        <PasswordInput label="Kerberos Keytab (Base64)" {...form.getInputProps('kerberos_keytab')} />
        <TextInput label="Connection URI" {...form.getInputProps('connection_uri')} />
        <Textarea
          label="Extra (JSON)"
          placeholder='{"ssl": true, "timeout": 10}'
          minRows={3}
          {...form.getInputProps('extra')}
        />

        <Group justify="flex-end" mt="md">
          <Button type="submit">Create Integration</Button>
        </Group>
      </form>
    </Box>
  );
}
