/** Schema API - Table and database exploration */

import apiClient from './client';
import type { TableInfo } from '../types';

export const schemaApi = {
    /**
     * List available tables
     */
    async listTables(
        database?: string,
        catalog?: string,
        search?: string
    ): Promise<TableInfo[]> {
        const params = new URLSearchParams();
        if (database) params.append('database', database);
        if (catalog) params.append('catalog', catalog);
        if (search) params.append('search', search);

        const query = params.toString();
        return apiClient.get<TableInfo[]>(`/schema/tables${query ? `?${query}` : ''}`);
    },

    /**
     * Get table details
     */
    async getTable(
        tableName: string,
        database?: string,
        catalog?: string
    ): Promise<TableInfo> {
        const params = new URLSearchParams();
        if (database) params.append('database', database);
        if (catalog) params.append('catalog', catalog);

        const query = params.toString();
        return apiClient.get<TableInfo>(
            `/schema/table/${tableName}${query ? `?${query}` : ''}`
        );
    },

    /**
     * List available databases
     */
    async listDatabases(catalog?: string): Promise<string[]> {
        const query = catalog ? `?catalog=${catalog}` : '';
        return apiClient.get<string[]>(`/schema/databases${query}`);
    },

    /**
     * Semantic search across schema
     */
    async searchSchema(query: string, topK = 10): Promise<TableInfo[]> {
        return apiClient.get<TableInfo[]>(
            `/schema/search?query=${encodeURIComponent(query)}&top_k=${topK}`
        );
    },
};

export default schemaApi;
