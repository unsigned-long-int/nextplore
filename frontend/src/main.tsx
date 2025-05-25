import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import {
  MantineProvider,
  ColorSchemeScript,
  createTheme,
} from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { MsalProvider } from '@azure/msal-react';
import { msalInstance } from './msalInstance';

const theme = createTheme({
  primaryColor: 'grape',
  defaultRadius: 'md',
  fontFamily: 'Inter, sans-serif',
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ColorSchemeScript defaultColorScheme="dark" />
    <MsalProvider instance={msalInstance}>
      <MantineProvider theme={theme} defaultColorScheme="dark">
        <Notifications />
        <App />
      </MantineProvider>
    </MsalProvider>
  </React.StrictMode>
);