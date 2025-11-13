import { ApiError} from './errors.ts';

export type CreateHttpOptions = {
    baseURL: string;
    scopes: string[];
    getBearer: (scopes: string[]) => Promise<string>;
    onUnauthorized?: () => void;
};

export const createHttp = ({ baseURL, scopes, getBearer, onUnauthorized }: CreateHttpOptions) => {
    const withAuth = async (init?: RequestInit) => {
        const token = await getBearer(scopes);
        const headers = new Headers(init?.headers || {});
        if (!headers.has('Authorization')) {
            headers.set('Authorization', `${token}`);
        }
        return {...init, headers};
    };
    const  withJsonBody = (init: RequestInit | undefined, body: unknown): RequestInit => {
        const headers = new Headers(init?.headers || {});
        if (body !== undefined && body !== null) {
                if (!headers.has('Content-Type')) {
                    headers.set('Content-Type', 'application/json');
                }
            const payload = typeof body === 'string' ? body : JSON.stringify(body);
            return { ...init, headers, body: payload };
        }
        return { ...init, headers };
  }

    async function request<T>(path: string, init?: RequestInit): Promise<T> {
        const res = await fetch(new URL(path, baseURL), await withAuth(init));
        const contentType = res.headers.get('content-type') || '';
        const isJson = contentType.includes('application/json');
        const body = isJson
            ? await res.json().catch(() => undefined)
            : await res.text().catch(() => undefined);

        if (!res.ok) {
            if(res.status === 401 && onUnauthorized) onUnauthorized();
            throw new ApiError(`HTTP ${res.status}`, res.status, body);
        }
        return body as T;
    };

    return {
        get<T>(path: string, init?: RequestInit) {
            return request<T>(path, {...init, method: 'GET'});
        },
        post<T, B = unknown>(path: string, body?: B, init?: RequestInit) {
            return request<T>(path, withJsonBody({...init, method: 'POST'}, body));
        },
        patch<T, B = unknown>(path: string, body?: B, init?: RequestInit) {
            return request<T>(path, withJsonBody({...init, method: 'PATCH'}, body));
        },
        delete<T>(path: string, init?: RequestInit) {
            return request<T>(path, {...init, method: 'DELETE'});
        }
    }
};

export type Http = ReturnType<typeof createHttp>;