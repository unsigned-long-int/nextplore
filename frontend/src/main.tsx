import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  MantineProvider,
  ColorSchemeScript,
  createTheme,
} from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { MsalProvider } from '@azure/msal-react';
import { BrowserRouter } from 'react-router-dom';
import { msalInstance } from './authentication/authProvider';
import { AuthRedirectHandler } from './components/AuthRedirectHandler';

const theme = createTheme({
  primaryColor: 'grape',
  defaultRadius: 'md',
  fontFamily: 'Inter, sans-serif',
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <React.StrictMode>
      <ColorSchemeScript defaultColorScheme="dark" />
      <MsalProvider instance={msalInstance}>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          <Notifications />
          <AuthRedirectHandler/>
        </MantineProvider>
      </MsalProvider>
    </React.StrictMode>
  </BrowserRouter>
);