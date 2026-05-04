import { Anchor, Center, Container, Paper, Stack, Text, Title } from '@mantine/core';

export const SuspendedPage = () => (
    <Center mih="100vh">
        <Container size="sm" w="100%">
            <Paper withBorder p="xl" ta="center">
                <Stack gap="md" align="center">
                    <Title order={3}>Access suspended</Title>

                    <Text c="dimmed">
                        Your organisation's access has been suspended.
                        Please contact{' '}
                        <Anchor href="mailto:admin@nextplore.co">
                            admin@nextplore.co
                        </Anchor>
                        {' '}to resolve this.
                    </Text>
                </Stack>
            </Paper>
        </Container>
    </Center>
);