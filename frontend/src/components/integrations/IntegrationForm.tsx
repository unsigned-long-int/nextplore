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
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { showNotification } from '@mantine/notifications';
import {
    IconCheck,
    IconX
} from "@tabler/icons-react";
import { useState } from "react";

import { useTestIntegration } from "../../hooks/useTestIntegration";
import type {
    IntegrationCreateRequest,
    IntegrationFormProps,
} from "../../interface/integration-create-request.interface";

export const IntegrationForm: React.FC<IntegrationFormProps> = ({
  service_type,
  onSubmit,
}) => {
  const [testing, setTesting] = useState(false);
  const { testIntegration } = useTestIntegration();

  const integrationRequestForm = useForm<IntegrationCreateRequest>({
    initialValues: {
      service_type: service_type,
      auth_method: "",
      connection_name: "",
      host: "",
      port: 0,
      database_name: "",
      username: "",
      password: "",
      kerberos_principal: "",
      windows_domain: "",
      extra_options: "",
      autosync_on: true,
    },
  });

  const handleSubmit = (values: IntegrationCreateRequest) => {
    onSubmit(values);
  };

  const handleTest = async (values: IntegrationCreateRequest) => {
        setTesting(true);
        try {
            const result = await testIntegration(values);
            if (!result.success) throw new Error(!result.message ? 'Unhandled Error': result.message);
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
    <Box maw={600} mx="auto">
      <Group justify="space-between" align="center" mb="md">
        <Title order={3}>Create Integration</Title>
        <Switch
          label="Auto Sync"
          onLabel="ON"
          offLabel="OFF"
          size="lg"
          {...integrationRequestForm.getInputProps("autosync_on", {
            type: "checkbox",
          })}
        />
      </Group>
      <form onSubmit={integrationRequestForm.onSubmit(handleSubmit)}>
        <TextInput label="Service Type" value={service_type} readOnly />
        <Select
          label="Auth Method"
          placeholder="e.g. direct, ODBC, JDBC"
          data={["basic", "odbc", "jdbc", "kerberos"]}
          {...integrationRequestForm.getInputProps("auth_method")}
        />
        <TextInput
          label="Connection Name"
          {...integrationRequestForm.getInputProps("connection_name")}
        />
        <TextInput
          label="Host"
          {...integrationRequestForm.getInputProps("host")}
        />
        <NumberInput
          label="Port"
          {...integrationRequestForm.getInputProps("port")}
        />
        <TextInput
          label="Database Name"
          {...integrationRequestForm.getInputProps("database_name")}
        />
        <TextInput
          label="Username"
          {...integrationRequestForm.getInputProps("username")}
        />
        <PasswordInput
          label="Password"
          {...integrationRequestForm.getInputProps("password")}
        />
        <TextInput
          label="Kerberos Principal"
          {...integrationRequestForm.getInputProps("kerberos_principal")}
        />
        <TextInput
          label="Windows Domain"
          {...integrationRequestForm.getInputProps("windows_domain")}
        />
        <Textarea
          label="Extra (JSON)"
          placeholder="{'ssl': true, 'timeout': 10}"
          minRows={3}
          {...integrationRequestForm.getInputProps("extra_options")}
        />

        <Group justify="flex-end" mt="md">
          <Button
            variant="default"
            onClick={() => handleTest(integrationRequestForm.values)}
            loading={testing}
          >
            Test Integration
          </Button>
          <Button type="submit">Create Integration</Button>
        </Group>
      </form>
    </Box>
  );
};
