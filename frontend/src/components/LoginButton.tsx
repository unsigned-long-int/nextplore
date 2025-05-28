import { useMsal } from '@azure/msal-react';
import { Button, Menu, Avatar } from '@mantine/core';
import { loginRequest } from '../authentication/authConfig';
import { NavigationBar } from '../components/NavigationBar';
import { Outlet } from 'react-router-dom';


export const LoginButton = () => {
    const { instance, accounts } = useMsal();
    const isAuth = accounts.length > 0;
    const user = isAuth ? accounts[0] : null;

    return isAuth ? (
        <Menu shadow='md' width={200}>
            <NavigationBar />
            <main className="main-content">
                <Outlet />
            </main>
        <Menu.Target>
            <Avatar radius='xl' size='sm' color='grape' alt={user?.name}>
            {user?.name?.[0] || 'U'}
            </Avatar>
        </Menu.Target>
        <Menu.Dropdown>
            <Menu.Label>{user?.name}</Menu.Label>
            <Menu.Item onClick={() => instance.logoutRedirect()}>Logout</Menu.Item>
        </Menu.Dropdown>
        </Menu>
    ) : (
        <Button onClick={() => instance.loginRedirect(loginRequest)}>Login with Microsoft</Button>
    );
};