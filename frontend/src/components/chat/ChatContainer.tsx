/** ChatContainer component with prominent ClearSky logo */

import { useRef, useEffect } from 'react';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';
import { ThinkingIndicator } from './ThinkingIndicator';
import type { ChatMessage as ChatMessageType } from '../../types';
import type { AgentStep } from '../../hooks/useChat';

interface ChatContainerProps {
    messages: ChatMessageType[];
    loading: boolean;
    thinkingSteps: AgentStep[];
    sessionId?: string | null;
    onSubmit: (question: string) => void;
}

export function ChatContainer({ messages, loading, thinkingSteps, sessionId, onSubmit }: ChatContainerProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, thinkingSteps]);

    return (
        <div className="flex flex-col h-full">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 && !loading ? (
                    <div className="h-full flex flex-col items-center justify-center">
                        {/* Prominent ClearSky Logo */}
                        <div className="mb-8 text-center">
                            <img
                                src="/clearsky-logo.png"
                                alt="ClearSky"
                                className="h-32 w-32 mx-auto mb-6 rounded-2xl shadow-2xl shadow-primary-500/20"
                            />
                            <h1 className="text-4xl font-bold gradient-text mb-3">
                                ClearSky
                            </h1>
                            <p className="text-xl text-surface-300 mb-2">
                                Text-to-SQL Assistant
                            </p>
                            <p className="text-surface-400 text-sm max-w-md mx-auto">
                                Ask questions in natural language. The AI agent will analyze your schema,
                                generate SQL, and self-correct if needed.
                            </p>
                        </div>

                        {/* Subtle hint */}
                        <div className="text-center text-surface-500 text-sm">
                            <p>💡 Try sample questions from the sidebar or type your own below</p>
                        </div>
                    </div>
                ) : (
                    <>
                        {messages.map((message) => (
                            <ChatMessage key={message.id} message={message} sessionId={sessionId || undefined} />
                        ))}

                        {/* Show thinking indicator while loading */}
                        {loading && (
                            <ThinkingIndicator
                                steps={thinkingSteps}
                                isLoading={loading}
                            />
                        )}
                    </>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="p-6 border-t border-surface-700">
                <ChatInput onSubmit={onSubmit} loading={loading} />
            </div>
        </div>
    );
}

export default ChatContainer;
