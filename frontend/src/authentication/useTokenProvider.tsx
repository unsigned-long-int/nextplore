import { InteractionRequiredAuthError, InteractionStatus} from "@azure/msal-browser";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./authConfig";

export function useTokenProvider() {
    const { instance, inProgress, accounts } = useMsal();

    const getToken = async (): Promise<string | null> => {
        if (inProgress === InteractionStatus.None) {
            const activeAccount = accounts[0];
            if (!activeAccount) return null;
            
            try {
                const response = await instance.acquireTokenSilent({
                    ...loginRequest,
                    account: activeAccount
                });
                return response.accessToken;
            } catch (e) {
                if (e instanceof InteractionRequiredAuthError) {
                    const response = await instance.acquireTokenPopup(loginRequest);
                    return response.accessToken;
                }
            }
            return null;
        }
        return null;
    };

    return { getToken };
}