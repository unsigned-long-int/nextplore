import { AppShell, Title, Container, Group, rem } from '@mantine/core';
import { IconDatabase } from '@tabler/icons-react';
import { QueryPage } from './pages/QueryPage';

function App() {
  return (
    <AppShell
      header={{ height: 60 }}
      padding="md"
    >
      <AppShell.Header>
        <Group justify="space-between" px="md" h="100%">
          <Group gap="xs">
            <IconDatabase size={rem(22)} />
            <Title order={3}>Nextplore</Title>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        <Container size="lg">
          <QueryPage />
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}

export default App;