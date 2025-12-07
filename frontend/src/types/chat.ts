/** Chat-related TypeScript types */

import { ChartConfig } from './visualization';

export interface QueryOptions {
    max_rows?: number;
    catalog?: string;
    database?: string;
    environment?: 'UAT' | 'PROD';
    debug?: boolean;
    explain_sql?: boolean;
    visualization_mode?: 'auto' | 'table_only' | 'chart_only';
    allow_advanced_charts?: boolean;
}

export interface QueryRequest {
    session_id?: string;
    question: string;
    options?: QueryOptions;
}

export interface ResultPreview {
    columns: string[];
    rows: unknown[][];
    total_rows: number;
    truncated: boolean;
}

export interface AgentStep {
    step_id: string;
    step_type: string;
    description: string;
    timestamp: string;
    details?: Record<string, unknown>;
}

export interface QueryError {
    message: string;
    details?: string;
    error_type?: string;
}

export type QueryStatus = 'running' | 'completed' | 'failed';

export interface QueryResponse {
    session_id: string;
    message_id: string;
    status: QueryStatus;
    answer_summary?: string;
    sql?: string;
    sql_explanation?: string;
    result_preview?: ResultPreview;
    quick_chart?: ChartConfig | null;
    alternative_charts?: ChartConfig[] | null;
    s3_result_url?: string | null;
    intermediate_steps?: AgentStep[] | null;
    error?: QueryError | null;
    execution_time_ms?: number;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    response?: QueryResponse;
}

export interface ChatSession {
    id: string;
    title?: string;
    created_at: string;
    updated_at: string;
    messages: ChatMessage[];
    metadata?: Record<string, unknown>;
}

export interface SessionListItem {
    id: string;
    title?: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    last_question?: string;
}

export interface UpdatesResponse {
    session_id: string;
    message_id: string;
    status: QueryStatus;
    partial_summary?: string;
    partial_sql?: string;
    current_step?: string;
    progress_percent?: number;
}
