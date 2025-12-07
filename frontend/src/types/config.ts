/** Configuration TypeScript types */

export interface FrontendConfig {
    app_name: string;
    version: string;
    enable_advanced_charts: boolean;
    enable_streaming: boolean;
    default_max_rows: number;
    enable_sql_explanation: boolean;
    enable_debug_mode: boolean;
}

export interface FeatureFlags {
    enable_streaming: boolean;
    enable_advanced_charts: boolean;
    enable_sql_explanation: boolean;
    enable_debug_mode: boolean;
    default_max_rows: number;
}
