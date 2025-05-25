import { useMsal } from '@azure/msal-react';
import { Button, Menu, Avatar } from '@mantine/core';

export const LoginButton = () => {
  const { instance, accounts } = useMsal();
  const isAuthenticated = accounts.length > 0;
  const user = isAuthenticated ? accounts[0] : null;

  const handleLogin = () => {
    instance.loginRedirect({
        scopes: ['openid', 'profile', 'email'],
    });
  };

  const handleLogout = () => {
    instance.logoutRedirect();
  };

  if (!isAuthenticated) {
    return <Button onClick={handleLogin}>Login with Microsoft</Button>;
  }

  return (
    <Menu shadow="md" width={200}>
      <Menu.Target>
        <Avatar
          radius="xl"
          size="sm"
          color="grape"
          alt={user?.name}
        >
          {user?.name?.[0] ?? 'U'}
        </Avatar>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>{user?.name || 'Signed in'}</Menu.Label>
        <Menu.Item onClick={handleLogout}>Logout</Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
};