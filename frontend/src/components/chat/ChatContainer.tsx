/** ChatContainer component with agent thinking display */

import { useRef, useEffect } from 'react';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';
import { ThinkingIndicator } from './ThinkingIndicator';
import { Card } from '../common';
import { Sparkles } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types';
import type { AgentStep } from '../../hooks/useChat';

interface ChatContainerProps {
    messages: ChatMessageType[];
    loading: boolean;
    thinkingSteps: AgentStep[];
    onSubmit: (question: string) => void;
}

export function ChatContainer({ messages, loading, thinkingSteps, onSubmit }: ChatContainerProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, thinkingSteps]);

    return (
        <div className="flex flex-col h-full">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 && !loading ? (
                    <div className="h-full flex items-center justify-center">
                        <Card className="max-w-md text-center p-8">
                            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-400 to-accent-500 mx-auto flex items-center justify-center mb-4">
                                <Sparkles className="h-8 w-8 text-white" />
                            </div>
                            <h2 className="text-xl font-semibold text-surface-100 mb-2">
                                Ask About Your Data
                            </h2>
                            <p className="text-surface-400 text-sm mb-6">
                                Ask questions in natural language. The AI agent will analyze your schema, generate SQL, and self-correct if needed.
                            </p>
                            <div className="space-y-2 text-left">
                                <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">
                                    Try asking:
                                </p>
                                {[
                                    "Show all customers",
                                    "Show total order amount by customer",
                                    "What products have low stock?",
                                ].map((example, i) => (
                                    <button
                                        key={i}
                                        onClick={() => onSubmit(example)}
                                        className="w-full text-left text-sm px-3 py-2 rounded-lg bg-surface-800/50 text-surface-300 hover:bg-surface-700/50 hover:text-surface-100 transition-smooth"
                                    >
                                        "{example}"
                                    </button>
                                ))}
                            </div>
                        </Card>
                    </div>
                ) : (
                    <>
                        {messages.map((message) => (
                            <ChatMessage key={message.id} message={message} />
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
