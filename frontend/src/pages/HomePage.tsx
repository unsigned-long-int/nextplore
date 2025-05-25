import { Container, Title, Text } from '@mantine/core';
import { LoginButton } from '../components/LoginButton';

export const HomePage = () => {
    return (
        <Container size="sm" mt="xl">
            <Title order={1}>
                Welcome to Nextplore
            </Title>
            <Text mt="sm">Connect, explore, and query any database using GenUI.</Text>
            <LoginButton/>
        </Container>
    );
};