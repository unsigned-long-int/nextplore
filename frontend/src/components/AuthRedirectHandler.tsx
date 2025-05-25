import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useMsal } from '@azure/msal-react';
import { msalInstance } from '../msalInstance';

export const AuthRedirectHandler = () => {
    const { instance, accounts } = useMsal();
    const navigate = useNavigate();

  useEffect(() => {
    const account = instance.getActiveAccount();
    if (!account && accounts.length > 0) {
        instance.setActiveAccount(accounts[0]);
        navigate('/querypage');
    } else if (account) {
        navigate('/querypage');
    }
  }, [instance, accounts, navigate]);
  
  return null;
};