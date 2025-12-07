/** useChat - Manage chat state, queries, and agent thinking stream */

import { useState, useCallback, useRef, useEffect } from 'react';
import { chatApi } from '../api';
import type {
    QueryRequest,
    QueryResponse,
    ChatMessage,
} from '../types';

export interface AgentStep {
    type: string;
    description: string;
    details?: Record<string, unknown>;
    timestamp: string;
}

interface UseChatReturn {
    messages: ChatMessage[];
    currentResponse: QueryResponse | null;
    loading: boolean;
    error: string | null;
    sessionId: string | null;
    thinkingSteps: AgentStep[];
    submitQuery: (question: string, options?: QueryRequest['options']) => Promise<void>;
    clearMessages: () => void;
    loadSession: (sessionId: string) => Promise<void>;
}

const API_BASE = '/api';

export function useChat(): UseChatReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [currentResponse, setCurrentResponse] = useState<QueryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [thinkingSteps, setThinkingSteps] = useState<AgentStep[]>([]);
    const eventSourceRef = useRef<EventSource | null>(null);
    const pendingMessageIdRef = useRef<string | null>(null);

    // Cleanup EventSource on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    const fetchFinalResult = useCallback(async (messageId: string) => {
        try {
            const response = await fetch(`${API_BASE}/chat/result/${messageId}`);
            if (response.ok) {
                const result: QueryResponse = await response.json();
                setCurrentResponse(result);

                // Add assistant message with full response
                const assistantMessage: ChatMessage = {
                    id: result.message_id,
                    role: 'assistant',
                    content: result.answer_summary || '',
                    timestamp: new Date().toISOString(),
                    response: result,
                };
                setMessages((prev) => {
                    // Replace placeholder message with full response
                    const filtered = prev.filter(m => m.id !== messageId);
                    return [...filtered, assistantMessage];
                });

                if (result.error) {
                    setError(result.error.message);
                }
            }
        } catch (err) {
            console.error('Failed to fetch final result:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const startThinkingStream = useCallback((messageId: string) => {
        // Close any existing stream
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        setThinkingSteps([]);
        pendingMessageIdRef.current = messageId;

        // Connect to SSE endpoint
        const eventSource = new EventSource(`${API_BASE}/chat/stream/${messageId}`);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
            try {
                const step: AgentStep = JSON.parse(event.data);

                // Skip heartbeats from display
                if (step.type !== 'heartbeat') {
                    setThinkingSteps((prev) => [...prev, step]);
                }

                if (step.type === 'done') {
                    eventSource.close();
                    eventSourceRef.current = null;
                    // Fetch the final result
                    if (pendingMessageIdRef.current) {
                        fetchFinalResult(pendingMessageIdRef.current);
                    }
                } else if (step.type === 'error') {
                    eventSource.close();
                    eventSourceRef.current = null;
                    setLoading(false);
                    setError(step.description || 'An error occurred');
                }
            } catch (err) {
                console.error('Failed to parse SSE event:', err);
            }
        };

        eventSource.onerror = (err) => {
            console.error('SSE error:', err);
            eventSource.close();
            eventSourceRef.current = null;
            // Try to fetch result anyway
            if (pendingMessageIdRef.current) {
                fetchFinalResult(pendingMessageIdRef.current);
            }
        };
    }, [fetchFinalResult]);

    const submitQuery = useCallback(
        async (question: string, options?: QueryRequest['options']) => {
            setLoading(true);
            setError(null);
            setThinkingSteps([]);

            // Add user message
            const userMessage: ChatMessage = {
                id: `user-${Date.now()}`,
                role: 'user',
                content: question,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, userMessage]);

            try {
                const request: QueryRequest = {
                    session_id: sessionId || undefined,
                    question,
                    options: {
                        ...options,
                        debug: true, // Enable debug for thinking steps
                    },
                };

                // Submit the query - this returns immediately with message_id
                const response = await chatApi.submitQuery(request);
                setSessionId(response.session_id);

                // Add placeholder assistant message
                const placeholderMessage: ChatMessage = {
                    id: response.message_id,
                    role: 'assistant',
                    content: 'Thinking...',
                    timestamp: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, placeholderMessage]);

                // Start listening to thinking stream IMMEDIATELY
                startThinkingStream(response.message_id);

            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : 'Query failed';
                setError(errorMessage);
                setLoading(false);

                // Add error message
                const errorAssistantMessage: ChatMessage = {
                    id: `error-${Date.now()}`,
                    role: 'assistant',
                    content: `Error: ${errorMessage}`,
                    timestamp: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, errorAssistantMessage]);
            }
        },
        [sessionId, startThinkingStream]
    );

    const loadSession = useCallback(async (sid: string) => {
        try {
            setLoading(true);
            const session = await chatApi.getSession(sid);
            setSessionId(session.id);
            setMessages(session.messages);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load session');
        } finally {
            setLoading(false);
        }
    }, []);

    const clearMessages = useCallback(() => {
        setMessages([]);
        setSessionId(null);
        setCurrentResponse(null);
        setError(null);
        setThinkingSteps([]);
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
    }, []);

    return {
        messages,
        currentResponse,
        loading,
        error,
        sessionId,
        thinkingSteps,
        submitQuery,
        clearMessages,
        loadSession,
    };
}

export default useChat;
