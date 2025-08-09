import { Center, Paper, Stack, Text, Title } from '@mantine/core';
import { LoginButton } from '../components/LoginButton';
import { LightRays } from '../components/login/LoginPageBackground';
import classes from '../styles/LoginPage.module.css';

export const LoginPage = () => {
  return (
    <div className={classes.wrapper}>
      <div className={classes.gradientLayer} />

      <LightRays
        className={classes.raysLayer}
        raysOrigin="top-center"
        raysColor='#ffffff'
        raysSpeed={1}
        lightSpread={0.5}
        rayLength={3}
        pulsating
        fadeDistance={1.0}
        saturation={1.0}
        followMouse
        mouseInfluence={0.12}
        noiseAmount={0}
        distortion={0}
      />


      <Center className={classes.center}>
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

export default LoginPage;
