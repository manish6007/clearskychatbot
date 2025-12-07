/** ChatPage - Main chat interface with agent thinking display */

import { useEffect } from 'react';
import { ChatContainer } from '../components/chat';
import { useChat } from '../hooks';
import { useQuestion } from '../contexts';

export function ChatPage() {
    const { messages, loading, thinkingSteps, submitQuery } = useChat();
    const { pendingQuestion, clearPendingQuestion } = useQuestion();

    // Handle pending questions from sidebar
    useEffect(() => {
        if (pendingQuestion && !loading) {
            submitQuery(pendingQuestion);
            clearPendingQuestion();
        }
    }, [pendingQuestion, loading, submitQuery, clearPendingQuestion]);

    return (
        <div className="h-full -m-6">
            <ChatContainer
                messages={messages}
                loading={loading}
                thinkingSteps={thinkingSteps}
                onSubmit={submitQuery}
            />
        </div>
    );
}

export default ChatPage;
