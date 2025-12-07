/** useSchema - Manage schema exploration */

import { useState, useCallback, useEffect } from 'react';
import { schemaApi } from '../api';
import type { TableInfo } from '../types';

interface UseSchemaReturn {
    tables: TableInfo[];
    selectedTable: TableInfo | null;
    databases: string[];
    loading: boolean;
    error: string | null;
    searchTables: (query: string) => Promise<void>;
    selectTable: (tableName: string) => Promise<void>;
    loadTables: (database?: string) => Promise<void>;
    loadDatabases: () => Promise<void>;
}

export function useSchema(): UseSchemaReturn {
    const [tables, setTables] = useState<TableInfo[]>([]);
    const [selectedTable, setSelectedTable] = useState<TableInfo | null>(null);
    const [databases, setDatabases] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadTables = useCallback(async (database?: string) => {
        try {
            setLoading(true);
            setError(null);
            const data = await schemaApi.listTables(database);
            setTables(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load tables');
        } finally {
            setLoading(false);
        }
    }, []);

    const loadDatabases = useCallback(async () => {
        try {
            const data = await schemaApi.listDatabases();
            setDatabases(data);
        } catch (err) {
            console.error('Failed to load databases:', err);
        }
    }, []);

    const searchTables = useCallback(async (query: string) => {
        if (!query.trim()) {
            await loadTables();
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const data = await schemaApi.searchSchema(query);
            setTables(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search failed');
        } finally {
            setLoading(false);
        }
    }, [loadTables]);

    const selectTable = useCallback(async (tableName: string) => {
        try {
            setLoading(true);
            const table = await schemaApi.getTable(tableName);
            setSelectedTable(table);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load table');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadTables();
        loadDatabases();
    }, [loadTables, loadDatabases]);

    return {
        tables,
        selectedTable,
        databases,
        loading,
        error,
        searchTables,
        selectTable,
        loadTables,
        loadDatabases,
    };
}

export default useSchema;
