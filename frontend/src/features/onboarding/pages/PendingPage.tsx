import { Button, Center, Container, Paper, Stack, Text, Title } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';

export const PendingPage = () => {
    const queryClient = useQueryClient();

    return (
        <Center mih="100vh">
            <Container size="sm" w="100%">
                <Paper withBorder p="xl" ta="center">
                    <Stack gap="md" align="center">
                        <Title order={3}>Request under review</Title>

                        <Text c="dimmed">
                            Your registration is being reviewed by our team.
                            You will receive an email when your access is approved.
                        </Text>

                        <Button
                            variant="outline"
                            onClick={() =>
                                queryClient.invalidateQueries({ queryKey: ['user-profile'] })
                            }
                        >
                            Check again
                        </Button>
                    </Stack>
                </Paper>
            </Container>
        </Center>
    );
};