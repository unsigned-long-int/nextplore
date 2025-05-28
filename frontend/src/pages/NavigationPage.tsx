import { useMsal } from '@azure/msal-react';
import { Outlet } from 'react-router-dom';

import { NavigationBar } from '../components/NavigationBar';
import { LoginPage } from './LoginPage';
import styles from '../styles/NavigationPage.module.css'

export const NavigationPage = () => {
    const { accounts } = useMsal();
    const isAuth = accounts.length > 0;
    return isAuth ? (
        <div className={styles.container}>
            <NavigationBar />
            <main className={styles.content}>
                <Outlet />
            </main>
        </div>
        ): (<LoginPage/>)
};