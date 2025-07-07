import { Container, Group, Text } from '@mantine/core';
import classes from '../styles/LoginPage.module.css';
import { LoginButton } from '../components/LoginButton';

export const LoginPage = () => {
  return (
    <div className={classes.wrapper}>
      <Container size={700} className={classes.inner}>
        <h1 className={classes.title}>
            Welcome to Nextplore
        </h1>

        <Text className={classes.description} c="dimmed">
            Connect, explore, and query any database using GenUI.
        </Text>

        <Group className={classes.controls}>
        <LoginButton/>
        </Group>
      </Container>
    </div>
  );
}