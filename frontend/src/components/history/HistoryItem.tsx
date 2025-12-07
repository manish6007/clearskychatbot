/** HistoryItem component */

import { MessageSquare, Trash2, Clock } from 'lucide-react';
import { Card, Button } from '../common';
import type { SessionListItem } from '../../types';

interface HistoryItemProps {
    session: SessionListItem;
    onSelect: () => void;
    onDelete: () => void;
}

export function HistoryItem({ session, onSelect, onDelete }: HistoryItemProps) {
    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = diffMs / (1000 * 60 * 60);

        if (diffHours < 1) {
            return 'Just now';
        } else if (diffHours < 24) {
            return `${Math.floor(diffHours)}h ago`;
        } else if (diffHours < 48) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString();
        }
    };

    return (
        <Card
            className="group glass-hover cursor-pointer"
            onClick={onSelect}
        >
            <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="h-5 w-5 text-surface-400" />
                </div>

                <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-surface-200 truncate">
                        {session.title || 'Untitled Session'}
                    </h3>
                    {session.last_question && (
                        <p className="text-sm text-surface-500 truncate mt-1">
                            {session.last_question}
                        </p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-surface-500">
                        <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDate(session.updated_at)}
                        </span>
                        <span>{session.message_count} messages</span>
                    </div>
                </div>

                <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                    }}
                >
                    <Trash2 className="h-4 w-4 text-red-400" />
                </Button>
            </div>
        </Card>
    );
}

export default HistoryItem;
