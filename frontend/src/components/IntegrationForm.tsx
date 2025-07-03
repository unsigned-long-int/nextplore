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
import { useState } from 'react';

import { useTestIntegration } from '../hooks/useTestIntegration';
import type { IntegrationCreateRequest, IntegrationFormProps } from '../interface/integration-create-request.interface';
  

export const IntegrationForm:  React.FC<IntegrationFormProps> = ({ service_type, onSubmit }) => {
    const [testResult, setTestResult] = useState<string | null>(null);
    const [testing, setTesting] = useState(false);
    const { testIntegration } = useTestIntegration();


    const integrationRequestForm = useForm<IntegrationCreateRequest>({
        initialValues: {
            service_type: service_type,
            auth_method: '',
            connection_name: '',
            host: '',
            port: 0,
            database_name: '',
            username: '',
            password: '',
            kerberos_principal: '',
            windows_domain: '',
            extra_options: ''
        }
    });
    
    const handleSubmit = (values: IntegrationCreateRequest) => {
        onSubmit(values);
    };

    const handleTest = async (values: IntegrationCreateRequest) => {
        setTesting(true);
        setTestResult(null);
        try {
            const response = await testIntegration(values);
            if (response.success) {
                setTestResult('Connection successful!');
            } else {
                setTestResult('Connection failed: ' + (response.data.message || 'Unknown error'));
            }
        } catch (error: any) {
            setTestResult('Error testing connection: ' + (error.response?.data?.detail || error.message));
        } finally {
            setTesting(false);
        }
    };

    return (
        <Box maw={600} mx='auto'>
            <Title order={3} mb='md'>Create Integration</Title>
    
            <form onSubmit={integrationRequestForm.onSubmit(handleSubmit)}>
                <TextInput
                    label='Service Type'
                    value={service_type}
                    readOnly
                />
                <Select
                    label='Auth Method'
                    placeholder='e.g. direct, ODBC, JDBC'
                    data={['basic', 'odbc', 'jdbc', 'kerberos']}
                    {...integrationRequestForm.getInputProps('auth_method')}
                />
                <TextInput label='Connection Name' {...integrationRequestForm.getInputProps('connection_name')} />
                <TextInput label='Host' {...integrationRequestForm.getInputProps('host')} />
                <NumberInput label='Port' {...integrationRequestForm.getInputProps('port')} />
                <TextInput label='Database Name' {...integrationRequestForm.getInputProps('database_name')} />
                <TextInput label='Username' {...integrationRequestForm.getInputProps('username')} />
                <PasswordInput label='Password' {...integrationRequestForm.getInputProps('password')} />
                <TextInput label='Kerberos Principal' {...integrationRequestForm.getInputProps('kerberos_principal')} />
                <TextInput label='Windows Domain' {...integrationRequestForm.getInputProps('windows_domain')} />
                <Textarea
                    label='Extra (JSON)'
                    placeholder="{'ssl': true, 'timeout': 10}"
                    minRows={3}
                    {...integrationRequestForm.getInputProps('extra_options')}
                />
        
                <Group justify='flex-end' mt='md'>
                    <Button
                        variant='default'
                        onClick={() => handleTest(integrationRequestForm.values)}
                        loading={testing}
                    >
                        Test Integration
                    </Button>                    
                    <Button type='submit'>Create Integration</Button>
                </Group>
            </form>
            {testResult && (
                <Box mt='md' style={{ color: testResult.includes('successful') ? 'green' : 'red' }}>
                    {testResult}
                </Box>
            )}
          </Box>
      );
}