/** FeedbackButtons component - Thumbs up/down feedback for query responses */

import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react';
import feedbackApi, { FeedbackType } from '../../api/feedbackApi';

interface FeedbackButtonsProps {
    messageId: string;
    sessionId: string;
    onFeedbackSubmitted?: (type: FeedbackType) => void;
}

export function FeedbackButtons({
    messageId,
    sessionId,
    onFeedbackSubmitted
}: FeedbackButtonsProps) {
    const [submitted, setSubmitted] = useState<FeedbackType | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFeedback = async (type: FeedbackType) => {
        if (submitted || isSubmitting) return;

        setIsSubmitting(true);
        setError(null);

        try {
            await feedbackApi.submit({
                message_id: messageId,
                session_id: sessionId,
                feedback_type: type,
            });
            setSubmitted(type);
            onFeedbackSubmitted?.(type);
        } catch (err) {
            console.error('Failed to submit feedback:', err);
            setError('Failed to submit feedback');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (submitted) {
        return (
            <div className="flex items-center gap-2 text-sm animate-fade-in">
                <span className="text-surface-400">
                    {submitted === 'thumbs_up'
                        ? '👍 Thanks for the feedback!'
                        : '👎 Thanks! We\'ll improve.'}
                </span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-3">
            <span className="text-sm text-surface-400">Was this helpful?</span>

            <div className="flex items-center gap-1">
                <button
                    onClick={() => handleFeedback('thumbs_up')}
                    disabled={isSubmitting}
                    className={`
                        p-2 rounded-lg transition-all duration-200
                        hover:bg-green-500/20 hover:text-green-400
                        disabled:opacity-50 disabled:cursor-not-allowed
                        ${isSubmitting ? 'animate-pulse' : ''}
                        text-surface-400 hover:scale-110
                    `}
                    title="Helpful"
                    aria-label="Mark as helpful"
                >
                    {isSubmitting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <ThumbsUp className="h-4 w-4" />
                    )}
                </button>

                <button
                    onClick={() => handleFeedback('thumbs_down')}
                    disabled={isSubmitting}
                    className={`
                        p-2 rounded-lg transition-all duration-200
                        hover:bg-red-500/20 hover:text-red-400
                        disabled:opacity-50 disabled:cursor-not-allowed
                        ${isSubmitting ? 'animate-pulse' : ''}
                        text-surface-400 hover:scale-110
                    `}
                    title="Not helpful"
                    aria-label="Mark as not helpful"
                >
                    {isSubmitting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <ThumbsDown className="h-4 w-4" />
                    )}
                </button>
            </div>

            {error && (
                <span className="text-xs text-red-400">{error}</span>
            )}
        </div>
    );
}

export default FeedbackButtons;
