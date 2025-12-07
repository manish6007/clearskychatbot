/** API Client - Base axios/fetch configuration */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

interface RequestOptions {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: unknown;
    headers?: Record<string, string>;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
        const { method = 'GET', body, headers = {} } = options;

        const url = `${this.baseUrl}${endpoint}`;

        const config: RequestInit = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...headers,
            },
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Request failed' }));
            throw new Error(error.detail || error.message || `HTTP ${response.status}`);
        }

        return response.json();
    }

    get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
        return this.request<T>(endpoint, { method: 'GET', headers });
    }

    post<T>(endpoint: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
        return this.request<T>(endpoint, { method: 'POST', body, headers });
    }

    put<T>(endpoint: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
        return this.request<T>(endpoint, { method: 'PUT', body, headers });
    }

    delete<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
        return this.request<T>(endpoint, { method: 'DELETE', headers });
    }
}

export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;
