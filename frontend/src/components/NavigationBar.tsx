import { useState } from 'react';
import {
  IconLogout,
  IconSettings,
  IconSwitchHorizontal,
  IconUser,
  IconInputAi,
  IconVector,
  IconCloudDataConnection
} from '@tabler/icons-react';
import { Code, Group } from '@mantine/core';
import classes from '../styles/NavigationBar.module.css';
import { useMsal } from '@azure/msal-react';
import { useNavigate, useLocation } from 'react-router-dom';

import svg from '../assets/trace.svg'

const data = [
  { location: '/user', label: 'User Profile', icon: IconUser },
  { location: '/query', label: 'AI Queries', icon: IconInputAi },
  { location: '/integrations', label: 'Integrations', icon: IconCloudDataConnection },
  { location: '/metadata', label: 'Metadata', icon: IconVector },
  { location: '/othersettings', label: 'Other Settings', icon: IconSettings },
];

export const NavigationBar = () => {
    const navigate = useNavigate();
    const current_location = useLocation();
    const { instance } = useMsal();
    const [active, setActive] = useState(current_location.pathname);

    const links = data.map((item) => (
        <a
        className={classes.location}
        data-active={item.location === active || undefined}
        key={item.location}
        onClick={(event) => {
            event.preventDefault();
            setActive(item.location);
            navigate(item.location);
        }}
        >
        <item.icon className={classes.linkIcon} stroke={1.5} />
        <span>{item.label}</span>
        </a>
    ));

    return (
        <nav className={classes.navbar}>
        <div className={classes.navbarMain}>
            <Group className={classes.header} justify='space-between'>
                <img src={svg} alt='Logo' height={80} width={80}/>
                <Code fw={700}>v1.0.0</Code>
            </Group>
            {links}
        </div>

        <div className={classes.footer}>
            <a href='#' className={classes.location} onClick={(event) => event.preventDefault()}>
            <IconSwitchHorizontal className={classes.linkIcon} stroke={1.5} />
            <span>Change account</span>
            </a>

            <a href='#' className={classes.location} onClick={() => instance.logoutRedirect()}>
            <IconLogout className={classes.linkIcon} stroke={1.5} />
            <span>Logout</span>
            </a>
        </div>
        </nav>
    );
}