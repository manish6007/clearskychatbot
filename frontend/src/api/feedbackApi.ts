/** Feedback API - Handle user feedback submission */

import apiClient from './client';

export type FeedbackType = 'thumbs_up' | 'thumbs_down';

export interface FeedbackRequest {
    message_id: string;
    session_id: string;
    feedback_type: FeedbackType;
    reason?: string;
}

export interface FeedbackResponse {
    success: boolean;
    feedback_id: string;
    message: string;
}

export interface FeedbackStats {
    total_feedback: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    success_rate: number;
    feedback_by_table: Record<string, { thumbs_up: number; thumbs_down: number }>;
    recent_patterns: Array<{
        question: string;
        sql_snippet: string;
        tables: string[];
        reason?: string;
    }>;
    active_hints: number;
}

export interface PolicyHint {
    id: string;
    hint_type: string;
    description: string;
    weight: number;
    tables: string[];
    pattern?: string;
    source_feedback_count: number;
}

export const feedbackApi = {
    /**
     * Submit user feedback for a query response
     */
    async submit(request: FeedbackRequest): Promise<FeedbackResponse> {
        return apiClient.post<FeedbackResponse>('/feedback/submit', request);
    },

    /**
     * Get aggregated feedback statistics
     */
    async getStats(): Promise<FeedbackStats> {
        return apiClient.get<FeedbackStats>('/feedback/stats');
    },

    /**
     * Get current policy hints
     */
    async getPolicyHints(): Promise<PolicyHint[]> {
        return apiClient.get<PolicyHint[]>('/feedback/policy-hints');
    },

    /**
     * Trigger policy analysis
     */
    async analyzePolicy(): Promise<{ success: boolean; message: string }> {
        return apiClient.post('/feedback/analyze', {});
    },
};

export default feedbackApi;
