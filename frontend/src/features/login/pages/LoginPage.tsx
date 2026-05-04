import { Center, Paper, Stack, Text, Title, Anchor, Divider } from '@mantine/core';
import svg from '@/assets/nextplore-logo-v-4.svg';
import { LoginButton } from '@/features/login/components/LoginButton';
import { LightRays } from '@/features/login/components/LoginBackground';
import classes from '@/styles/LoginPage.module.css';

export const LoginPage = () => {
    return (
        <div className={classes.wrapper}>
            <div className={classes.gradientLayer} />
            <LightRays
                className={classes.raysLayer}
                raysOrigin='top-center'
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
                <Paper className={classes.card} shadow='xl' radius='lg'>
                    <Stack gap='md' align='center'>
                        <img src={svg} alt='Logo' height={80} width={80} />
                        <Title className={classes.title}>
                            Welcome to <span className={classes.brand}>Nextplore</span>
                        </Title>
                        <Text size='md' className={classes.description}>
                            AI-powered insights. Secure. Instant. Beautiful.
                        </Text>

                        <LoginButton />

                        <Divider w="100%" label="New to Nextplore?" labelPosition="center" />

                        <Text size='sm' c='dimmed'>
                            Sign in with Microsoft to request access.{' '}
                            <Anchor
                                href="https://nextplore.co/contact"
                                target="_blank"
                                size="sm"
                            >
                                Learn more
                            </Anchor>
                        </Text>
                    </Stack>
                </Paper>
            </Center>
        </div>
    );
};
