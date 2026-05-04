import { Anchor, Center, Container, Paper, Stack, Text, Title } from '@mantine/core';

export const RejectedPage = () => (
    <Center mih="100vh">
        <Container size="sm" w="100%">
            <Paper withBorder p="xl" ta="center">
                <Stack gap="md" align="center">
                    <Title order={3}>Access not approved</Title>

                    <Text c="dimmed">
                        Unfortunately your access request was not approved.
                        Please contact{' '}
                        <Anchor href="mailto:admin@nextplore.co">
                            admin@nextplore.co
                        </Anchor>
                        {' '}if you believe this is an error.
                    </Text>
                </Stack>
            </Paper>
        </Container>
    </Center>
);