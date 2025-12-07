/** useHistory - Manage chat history */

import { useState, useCallback, useEffect } from 'react';
import { chatApi } from '../api';
import type { SessionListItem } from '../types';

interface UseHistoryReturn {
    sessions: SessionListItem[];
    loading: boolean;
    error: string | null;
    loadHistory: () => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
    refresh: () => Promise<void>;
}

export function useHistory(): UseHistoryReturn {
    const [sessions, setSessions] = useState<SessionListItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadHistory = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await chatApi.getHistory(50, 0);
            setSessions(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load history');
        } finally {
            setLoading(false);
        }
    }, []);

    const deleteSession = useCallback(async (sessionId: string) => {
        try {
            await chatApi.deleteSession(sessionId);
            setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete session');
        }
    }, []);

    const refresh = useCallback(async () => {
        await loadHistory();
    }, [loadHistory]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);

    return {
        sessions,
        loading,
        error,
        loadHistory,
        deleteSession,
        refresh,
    };
}

export default useHistory;
