/** useAppConfig - Load and manage app configuration */

import { useState, useEffect, useCallback } from 'react';
import { configApi } from '../api';
import type { FrontendConfig } from '../types';

interface UseAppConfigReturn {
    config: FrontendConfig | null;
    loading: boolean;
    error: string | null;
    reload: () => Promise<void>;
}

const defaultConfig: FrontendConfig = {
    app_name: 'ClearSky Text-to-SQL',
    version: '1.0.0',
    enable_advanced_charts: true,
    enable_streaming: true,
    default_max_rows: 1000,
    enable_sql_explanation: true,
    enable_debug_mode: false,
};

export function useAppConfig(): UseAppConfigReturn {
    const [config, setConfig] = useState<FrontendConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchConfig = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await configApi.getConfig();
            setConfig(data);
        } catch (err) {
            console.warn('Failed to load config, using defaults:', err);
            setConfig(defaultConfig);
            setError(err instanceof Error ? err.message : 'Failed to load config');
        } finally {
            setLoading(false);
        }
    }, []);

    const reload = useCallback(async () => {
        try {
            await configApi.reloadConfig();
            await fetchConfig();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to reload config');
        }
    }, [fetchConfig]);

    useEffect(() => {
        fetchConfig();
    }, [fetchConfig]);

    return { config, loading, error, reload };
}

export default useAppConfig;
