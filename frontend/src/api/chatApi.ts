/** Chat API - Query and session management */

import apiClient from './client';
import type {
    QueryRequest,
    QueryResponse,
    UpdatesResponse,
    ChatSession,
    SessionListItem,
} from '../types';

export const chatApi = {
    /**
     * Submit a natural language query
     */
    async submitQuery(request: QueryRequest): Promise<QueryResponse> {
        return apiClient.post<QueryResponse>('/chat/query', request);
    },

    /**
     * Poll for query updates
     */
    async getUpdates(sessionId: string, messageId: string): Promise<UpdatesResponse> {
        return apiClient.get<UpdatesResponse>(
            `/chat/updates?session_id=${sessionId}&message_id=${messageId}`
        );
    },

    /**
     * Get chat history
     */
    async getHistory(limit = 20, offset = 0): Promise<SessionListItem[]> {
        return apiClient.get<SessionListItem[]>(
            `/chat/history?limit=${limit}&offset=${offset}`
        );
    },

    /**
     * Get session details
     */
    async getSession(sessionId: string): Promise<ChatSession> {
        return apiClient.get<ChatSession>(`/chat/session/${sessionId}`);
    },

    /**
     * Delete a session
     */
    async deleteSession(sessionId: string): Promise<void> {
        return apiClient.delete(`/chat/session/${sessionId}`);
    },

    /**
     * Continue a session with a follow-up question
     */
    async continueSession(sessionId: string, question: string): Promise<QueryResponse> {
        return apiClient.post<QueryResponse>(`/chat/session/${sessionId}/continue`, {
            question,
        });
    },
};

export default chatApi;
