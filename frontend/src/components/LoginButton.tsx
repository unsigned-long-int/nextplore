import { useMsal } from '@azure/msal-react';
import { Avatar, Button, Menu } from '@mantine/core';
import { loginRequest } from '../authentication/authConfig';

export const LoginButton = () => {
  const { instance, accounts } = useMsal();
  const isAuth = accounts.length > 0;
  const user = isAuth ? accounts[0] : null;

  return isAuth ? (
    <Menu shadow="md" width={200}>
      <Menu.Target>
        <Avatar radius="xl" size="md" color="grape">
          {user?.name?.[0] || 'U'}
        </Avatar>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>{user?.name}</Menu.Label>
        <Menu.Item onClick={() => instance.logoutRedirect()}>Logout</Menu.Item>
      </Menu.Dropdown>
    </Menu>
  ) : (
    <Button size="md" radius="md" onClick={() => instance.loginRedirect(loginRequest)}>
      Login with Microsoft
    </Button>
  );
};
