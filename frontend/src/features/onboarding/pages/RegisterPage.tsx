import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Alert, Button, Center, Container,
    Loader, Paper, Select, Stack,
    Text, TextInput, Title,
} from '@mantine/core';
import { useRegisterCompany } from '@/features/onboarding/hooks/useRegisterCompany';

const PLANS = [
    { value: 'standard',   label: 'Standard'   },
    { value: 'growth',     label: 'Growth'      },
    { value: 'enterprise', label: 'Enterprise'  },
];

export const RegisterPage = () => {
    const navigate = useNavigate();
    const register = useRegisterCompany();

    const [form, setForm] = useState({
        company_name:  '',
        contact_email: '',
        plan:          'standard',
    });

    const set = (key: string) => (value: string) =>
        setForm(f => ({ ...f, [key]: value }));

    const submit = () => {
        if (!form.company_name || !form.contact_email) return;
        sessionStorage.setItem('register_email', form.contact_email);
        register.mutate(form, {
            onSuccess: () => navigate('/register/check-email'),
        });
    };

    return (
        <Center mih="100vh">
            <Container size="sm" w="100%">
                <Paper withBorder p="xl">
                    <Stack gap="md">
                        <div>
                            <Title order={3} mb={4}>
                                Request access to Nextplore
                            </Title>
                            <Text size="sm" c="dimmed">
                                Submit your details below. Our team will review
                                your request and notify you when approved.
                            </Text>
                        </div>

                        <TextInput
                            label="Company name"
                            value={form.company_name}
                            onChange={e => set('company_name')(e.target.value)}
                            disabled={register.isPending}
                        />

                        <TextInput
                            label="Work email"
                            type="email"
                            value={form.contact_email}
                            onChange={e => set('contact_email')(e.target.value)}
                            disabled={register.isPending}
                            description="Use your company email — we'll use the domain to identify your organisation."
                        />

                        <Select
                            label="Plan"
                            data={PLANS}
                            value={form.plan}
                            onChange={v => set('plan')(v ?? 'standard')}
                            disabled={register.isPending}
                            allowDeselect={false}
                        />

                        {register.isError && (
                            <Alert color="red">
                                {(register.error as Error)?.message
                                    ?? 'Registration failed. Please try again.'}
                            </Alert>
                        )}

                        <Button
                            size="md"
                            onClick={submit}
                            disabled={register.isPending || !form.company_name || !form.contact_email}
                            leftSection={register.isPending ? <Loader size={16} color="white" /> : null}
                        >
                            {register.isPending ? 'Submitting...' : 'Request access'}
                        </Button>
                    </Stack>
                </Paper>
            </Container>
        </Center>
    );
};