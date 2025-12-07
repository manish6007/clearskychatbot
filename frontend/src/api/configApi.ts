/** Config API - Frontend configuration */

import apiClient from './client';
import type { FrontendConfig, FeatureFlags } from '../types';

export const configApi = {
    /**
     * Get frontend configuration
     */
    async getConfig(): Promise<FrontendConfig> {
        return apiClient.get<FrontendConfig>('/config');
    },

    /**
     * Reload configuration from S3
     */
    async reloadConfig(): Promise<{ message: string; status: string }> {
        return apiClient.post('/config/reload');
    },

    /**
     * Health check
     */
    async healthCheck(): Promise<{ status: string; app_name?: string; version?: string }> {
        return apiClient.get('/config/health');
    },

    /**
     * Get feature flags only
     */
    async getFeatureFlags(): Promise<FeatureFlags> {
        return apiClient.get<FeatureFlags>('/config/features');
    },
};

export default configApi;
