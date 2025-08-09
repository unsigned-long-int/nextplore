import { MsalProvider } from '@azure/msal-react';
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
import { msalInstance } from './authentication/authProvider';
import { AuthRedirectHandler } from './components/AuthRedirectHandler';

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
        <MsalProvider instance={msalInstance}>
            <MantineProvider
            theme={theme}
            defaultColorScheme="dark"
            cssVariablesResolver={resolver}
            >
            <Notifications />
            <AuthRedirectHandler />
            </MantineProvider>
        </MsalProvider>
        </React.StrictMode>
    </BrowserRouter>
);
