/** ChatMessage component */

import { User, Bot } from 'lucide-react';
import { Card } from '../common';
import { QueryResult } from './QueryResult';
import type { ChatMessage as ChatMessageType } from '../../types';

interface ChatMessageProps {
    message: ChatMessageType;
    sessionId?: string;
}

export function ChatMessage({ message, sessionId }: ChatMessageProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
            {!isUser && (
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white" />
                </div>
            )}

            <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
                {isUser ? (
                    <Card variant="bordered" className="bg-primary-500/10 border-primary-500/30">
                        <p className="text-surface-100">{message.content}</p>
                    </Card>
                ) : message.response ? (
                    <QueryResult response={message.response} sessionId={sessionId} />
                ) : (
                    <Card className="bg-surface-800/50">
                        <p className="text-surface-100">{message.content}</p>
                    </Card>
                )}

                <span className="text-xs text-surface-500 mt-1 block">
                    {new Date(message.timestamp).toLocaleTimeString()}
                </span>
            </div>

            {isUser && (
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-surface-600 flex items-center justify-center">
                    <User className="h-5 w-5 text-surface-300" />
                </div>
            )}
        </div>
    );
}

export default ChatMessage;
