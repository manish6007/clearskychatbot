/** ChatPage - Main chat interface with agent thinking display */

import { ChatContainer } from '../components/chat';
import { useChat } from '../hooks';

export function ChatPage() {
    const { messages, loading, thinkingSteps, submitQuery } = useChat();

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
