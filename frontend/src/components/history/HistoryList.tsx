/** HistoryList component */

import { Clock, MessageSquare, Trash2 } from 'lucide-react';
import { Card, LoadingSpinner, Button } from '../common';
import { HistoryItem } from './HistoryItem';
import type { SessionListItem } from '../../types';

interface HistoryListProps {
    sessions: SessionListItem[];
    loading: boolean;
    onSelectSession: (sessionId: string) => void;
    onDeleteSession: (sessionId: string) => void;
}

export function HistoryList({
    sessions,
    loading,
    onSelectSession,
    onDeleteSession,
}: HistoryListProps) {
    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <LoadingSpinner />
            </div>
        );
    }

    if (sessions.length === 0) {
        return (
            <Card className="text-center py-12">
                <Clock className="h-12 w-12 text-surface-600 mx-auto mb-3" />
                <h3 className="text-lg font-medium text-surface-300 mb-1">No History Yet</h3>
                <p className="text-surface-500">Your chat sessions will appear here.</p>
            </Card>
        );
    }

    return (
        <div className="space-y-3">
            {sessions.map((session) => (
                <HistoryItem
                    key={session.id}
                    session={session}
                    onSelect={() => onSelectSession(session.id)}
                    onDelete={() => onDeleteSession(session.id)}
                />
            ))}
        </div>
    );
}

export default HistoryList;
