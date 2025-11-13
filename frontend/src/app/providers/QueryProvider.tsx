import { type ReactNode, useState } from 'react';
import {
    QueryClient,
    QueryClientProvider
} from '@tanstack/react-query';


export const QueryProvider = ({ children }: { children: ReactNode }) => {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        retry: (failureCount, error: any) => {
                            if (error?.status === 401 || error?.status === 403) return false;
                            return failureCount < 2;
                        },
                        refetchOnWindowFocus: false,
                        staleTime: 1000 * 60,
                    },
                    mutations: {
                        retry: 0,
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
};
