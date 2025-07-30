import { Center, Paper, Stack, Text, Title } from '@mantine/core';
import { LoginButton } from '../components/LoginButton';
import classes from '../styles/LoginPage.module.css';

export const LoginPage = () => {
  return (
    <div className={classes.wrapper}>
      <Center>
        <Paper className={classes.card} shadow="xl" radius="lg">
          <Stack gap="md" align="center">
            <Title className={classes.title}>
              Welcome to <span className={classes.brand}>Nextplore</span>
            </Title>
            <Text size="md" className={classes.description}>
              AI-powered insights. Secure. Instant. Beautiful.
            </Text>
            <LoginButton />
          </Stack>
        </Paper>
      </Center>
    </div>
  );
};
