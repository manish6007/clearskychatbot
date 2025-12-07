/** HistoryPage - Chat history */

import { useNavigate } from 'react-router-dom';
import { HistoryList } from '../components/history';
import { useHistory, useChat } from '../hooks';

export function HistoryPage() {
    const { sessions, loading, deleteSession } = useHistory();
    const { loadSession } = useChat();
    const navigate = useNavigate();

    const handleSelectSession = async (sessionId: string) => {
        await loadSession(sessionId);
        navigate('/');
    };

    return (
        <div>
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-100">Chat History</h1>
                <p className="text-surface-400 mt-1">
                    View and continue your previous conversations.
                </p>
            </div>

            <HistoryList
                sessions={sessions}
                loading={loading}
                onSelectSession={handleSelectSession}
                onDeleteSession={deleteSession}
            />
        </div>
    );
}

export default HistoryPage;
