import {
    Alert, Button, Center, Container,
    Loader, Paper, Stack, Text, Title,
} from '@mantine/core';

import { useResendVerification } from '@/features/onboarding/hooks/useResendVerification';


export const CheckEmailPage = () => {
    const resend = useResendVerification();

    return (
        <Center mih="100vh">
            <Container size="sm" w="100%">
                <Paper withBorder p="xl" ta="center">
                    <Stack gap="md" align="center">
                        <Title order={3}>Check your email</Title>

                        <Text c="dimmed">
                            We've sent a verification link to your work email.
                            Click the link to verify your address - then our team
                            will review your request.
                        </Text>

                        {resend.isSuccess && (
                            <Alert color="green" w="100%">
                                Verification email resent.
                            </Alert>
                        )}

                        {resend.isError && (
                            <Alert color="red" w="100%">
                                Failed to resend. Please try again.
                            </Alert>
                        )}

                        <Button
                            variant="outline"
                            size="sm"
                            disabled={resend.isPending}
                            leftSection={resend.isPending ? <Loader size={14} /> : null}
                            onClick={() => {
                                const contactEmail = sessionStorage.getItem('register_email') ?? '';
                                if (contactEmail) resend.mutate({ contactEmail });
                            }}
                        >
                            {resend.isPending ? 'Sending...' : 'Resend verification email'}
                        </Button>
                    </Stack>
                </Paper>
            </Container>
        </Center>
    );
};