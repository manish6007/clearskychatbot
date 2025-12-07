/** StatusBadge component */

import clsx from 'clsx';

interface StatusBadgeProps {
    status: 'running' | 'completed' | 'failed' | 'pending';
    className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
    const styles = {
        running: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        completed: 'bg-green-500/20 text-green-400 border-green-500/30',
        failed: 'bg-red-500/20 text-red-400 border-red-500/30',
        pending: 'bg-surface-500/20 text-surface-400 border-surface-500/30',
    };

    const labels = {
        running: 'Running',
        completed: 'Completed',
        failed: 'Failed',
        pending: 'Pending',
    };

    return (
        <span
            className={clsx(
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
                styles[status],
                className
            )}
        >
            {status === 'running' && (
                <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-yellow-400 animate-pulse" />
            )}
            {labels[status]}
        </span>
    );
}

export default StatusBadge;
