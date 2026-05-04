import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, Button, Center, Container, Paper, Stack, Text, Title } from '@mantine/core';
import { getAdminConsentUrl } from '@/shared/auth/msal';
import {useMsal} from "@azure/msal-react";

export const AdminConsentPage = () => {
    const navigate = useNavigate();
    const { accounts } = useMsal();

    const [params] = useSearchParams();
    const [granted, setGranted] = useState(false);
    const [denied,  setDenied]  = useState(false);

    const account = accounts[0];
    const tenantId = account?.tenantId;

    useEffect(() => {
        if (params.get('state') === 'admin_consent') {
            sessionStorage.clear();
            if (params.get('error')) { setDenied(true); return; }
            setGranted(true);
            setTimeout(() => navigate('/'), 2500);
        }
    }, [params, navigate]);

    if (granted) return (
        <Center mih="100vh">
            <Container size="sm">
                <Paper withBorder p="xl" ta="center">
                    <Alert color="green" mb="md">
                        Consent granted successfully.
                    </Alert>
                    <Text c="dimmed">Redirecting to sign in...</Text>
                </Paper>
            </Container>
        </Center>
    );

    return (
        <Center mih="100vh">
            <Container size="sm">
                <Paper withBorder p="xl">
                    <Stack gap="md">
                        <Title order={3}>Admin approval required</Title>

                        <Text c="dimmed">
                            Your organisation's IT policy requires an administrator
                            to approve Nextplore once before anyone in your company
                            can sign in. This is a one-time step.
                        </Text>

                        <Text c="dimmed">
                            If you are the IT admin, click below.
                            Otherwise, forward this page to your administrator.
                        </Text>

                        {denied && (
                            <Alert color="red">
                                Consent was declined. Ask your IT admin to try again.
                            </Alert>
                        )}

                        <Button
                            component="a"
                            href={getAdminConsentUrl(tenantId)}
                            size="md"
                            fullWidth
                        >
                            Grant admin consent for my organisation
                        </Button>

                        <Text size="xs" c="dimmed">
                            Nextplore only requests permission to read your profile
                            and call its own API - no access to email, files, or
                            other Microsoft services.
                        </Text>
                    </Stack>
                </Paper>
            </Container>
        </Center>
    );
};