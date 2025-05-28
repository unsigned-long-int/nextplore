import { useState } from 'react';
import {
  IconFingerprint,
  IconLogout,
  IconSettings,
  IconSwitchHorizontal,
  IconUser,
  IconInputAi,
  IconVector,
  IconCloudDataConnection
} from '@tabler/icons-react';
import { Group } from '@mantine/core';
import classes from '../styles/NavigationBar.module.css';
import { useMsal } from '@azure/msal-react';
import { useNavigate, useLocation } from 'react-router-dom';

const data = [
  { link: '/user', label: 'User Profile', icon: IconUser },
  { link: '/query', label: 'AI Queries', icon: IconInputAi },
  { link: '', label: 'Integrations', icon: IconCloudDataConnection },
  { link: '', label: 'Metadata', icon: IconVector },
  { link: '', label: 'My Secrets', icon: IconFingerprint },
  { link: '', label: 'Other Settings', icon: IconSettings },
];

export const NavigationBar = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { instance } = useMsal();
    const [active, setActive] = useState('User Profile');

    const links = data.map((item) => (
        <a
        className={classes.link}
        data-active={item.label === active || undefined}
        key={item.label}
        onClick={(event) => {
            event.preventDefault();
            setActive(item.label);
            navigate(item.link);
        }}
        >
        <item.icon className={classes.linkIcon} stroke={1.5} />
        <span>{item.label}</span>
        </a>
    ));

    return (
        <nav className={classes.navbar}>
        <div className={classes.navbarMain}>
            <Group className={classes.header} justify="space-between">
            </Group>
            {links}
        </div>

        <div className={classes.footer}>
            <a href="#" className={classes.link} onClick={(event) => event.preventDefault()}>
            <IconSwitchHorizontal className={classes.linkIcon} stroke={1.5} />
            <span>Change account</span>
            </a>

            <a href="#" className={classes.link} onClick={() => instance.logoutRedirect()}>
            <IconLogout className={classes.linkIcon} stroke={1.5} />
            <span>Logout</span>
            </a>
        </div>
        </nav>
    );
}