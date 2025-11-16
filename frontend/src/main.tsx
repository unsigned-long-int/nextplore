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
import { AuthPage } from '@/features/login/pages/AuthPage'
import { AppProviders } from '@/app/providers';

const theme = createTheme({
    primaryColor: 'grape',
    defaultRadius: 'md',
    fontFamily: 'Inter, sans-serif',
});

const resolver: CSSVariablesResolver = () => ({
    variables: {},
    light: {
        '--mantine-color-body': '#ffffff',
    },
    dark: {
        '--mantine-color-body': '#000312',
    },
});

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
