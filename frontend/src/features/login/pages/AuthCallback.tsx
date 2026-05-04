import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Center, Loader, Text } from '@mantine/core';
import { msalInstance, isConsentError } from '@/shared/auth/msal';


export const AuthCallback = () => {
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);


    useEffect(() => {
        msalInstance
            .handleRedirectPromise()
            .then((response) => {
                if (response?.account) {
                    msalInstance.setActiveAccount(response.account);
                }
                navigate('/', { replace: true });
            })
            .catch((e: unknown) => {
                const err = e as { errorCode?: string; message?: string };
                sessionStorage.removeItem('msal.interaction.status');

                if (isConsentError(err)) {
                    navigate('/admin-consent', { replace: true });
                    return;
                }
                setError(err.message ?? 'Authentication failed. Please try again.');
            });
    }, []);

    if (error) {
        return (
            <Center mih="100vh">
                <Text c="red" size="sm">{error}</Text>
            </Center>
        );
    }

    return (
        <Center mih="100vh">
            <Loader color="grape" />
        </Center>
    );
};