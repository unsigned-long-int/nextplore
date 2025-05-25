import { PublicClientApplication  } from "@azure/msal-browser";
import { msalConfig } from './authConfig';

export const msalInstance = new PublicClientApplication(msalConfig);

await msalInstance.initialize();


msalInstance.handleRedirectPromise().then((response) => {
    if (response) {
        msalInstance.setActiveAccount(response.account);
    } else {
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length > 0){
            msalInstance.setActiveAccount(accounts[0]);
        }
    }
});