import {
    ColorSchemeScript,
    MantineProvider,
    createTheme,
    type CSSVariablesResolver,
} from '@mantine/core';
import '@mantine/core/styles.css';
import { Notifications } from '@mantine/notifications';
import '@mantine/notifications/styles.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AppProviders } from '@/app/providers';
import { AuthPage } from '@/features/login/pages/AuthPage';
import { msalInstance } from '@/shared/auth/msal';

const theme = createTheme({
    primaryColor: 'grape',
    defaultRadius: 'md',
    fontFamily: 'Inter, sans-serif',
});

const resolver: CSSVariablesResolver = () => ({
    variables: {},
    light:  { '--mantine-color-body': '#ffffff' },
    dark:   { '--mantine-color-body': '#000312' },
});


msalInstance.initialize().then(() => {
    ReactDOM.createRoot(document.getElementById('root')!).render(
        <BrowserRouter>
            <React.StrictMode>
                <ColorSchemeScript defaultColorScheme="dark" />
                <AppProviders>
                    <MantineProvider
                        theme={theme}
                        defaultColorScheme="dark"
                        cssVariablesResolver={resolver}
                    >
                        <Notifications />
                        <AuthPage />
                    </MantineProvider>
                </AppProviders>
            </React.StrictMode>
        </BrowserRouter>
    );
});