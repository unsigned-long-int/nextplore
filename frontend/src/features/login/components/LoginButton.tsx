import { useMsal } from '@azure/msal-react';
import { Avatar, Button, Menu } from '@mantine/core';
import { login, logout } from '@/shared/auth/msal';
import { LOGIN_SCOPES } from '@/shared/auth/scopes';

export const LoginButton = () => {
    const { accounts } = useMsal();
    const isAuth = accounts.length > 0;
    const user = isAuth ? accounts[0] : null;

    return isAuth ? (
        <Menu shadow="md" width={200}>
            <Menu.Target>
                <Avatar radius="xl" size="md" color="grape">
                    {user?.name?.[0] ?? 'U'}
                </Avatar>
            </Menu.Target>
            <Menu.Dropdown>
                <Menu.Label>{user?.name}</Menu.Label>
                <Menu.Item onClick={() => logout()}>Logout</Menu.Item>
            </Menu.Dropdown>
        </Menu>
    ) : (
        <Button size="md" radius="md" onClick={() => login(LOGIN_SCOPES)}>
            Login with Microsoft
        </Button>
    );
};