import {
    Alert, Center, Container,
    Loader, Paper, Stack, Text, Title,
} from '@mantine/core';
import { useSearchParams } from 'react-router-dom';

import { useVerifyToken } from '@/features/onboarding/hooks/useVerifyToken';

export const VerifyEmailPage = () => {
    const [params] = useSearchParams();
    const token    = params.get('token') ?? '';
    const verify   = useVerifyToken(token);

    return (
        <Center mih="100vh">
            <Container size="sm" w="100%">
                <Paper withBorder p="xl" ta="center">
                    <Stack gap="md" align="center">
                        {verify.isLoading && <Loader />}

                        {verify.isSuccess && (
                            <>
                                <Title order={3}>Email verified</Title>
                                <Text c="dimmed">
                                    Your email is verified. Our team has been notified
                                    and will review your request shortly.
                                </Text>
                            </>
                        )}

                        {verify.isError && (
                            <Alert color="red" w="100%">
                                This verification link is invalid or has expired.
                                Please register again or request a new link.
                            </Alert>
                        )}
                    </Stack>
                </Paper>
            </Container>
        </Center>
    );
};