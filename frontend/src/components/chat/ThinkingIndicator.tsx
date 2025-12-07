/** ThinkingIndicator - Display agent thinking steps in real-time with full visibility */

import React from 'react';
import type { AgentStep } from '../../hooks/useChat';

interface ThinkingIndicatorProps {
    steps: AgentStep[];
    isLoading: boolean;
}

const stepConfig: Record<string, { icon: string; color: string; label: string }> = {
    start: { icon: '🚀', color: 'text-blue-400', label: 'Starting' },
    thinking: { icon: '💭', color: 'text-purple-400', label: 'Thinking' },
    agent_ready: { icon: '🤖', color: 'text-green-400', label: 'Agent Ready' },
    retrieval: { icon: '📊', color: 'text-cyan-400', label: 'Schema Retrieval' },
    memory: { icon: '💾', color: 'text-amber-400', label: 'Memory' },
    sql_generated: { icon: '✏️', color: 'text-yellow-400', label: 'SQL Generated' },
    sql_fixed: { icon: '🔧', color: 'text-orange-400', label: 'SQL Fixed' },
    executing: { icon: '⚡', color: 'text-blue-400', label: 'Executing Query' },
    success: { icon: '✅', color: 'text-green-400', label: 'Query Success' },
    error: { icon: '❌', color: 'text-red-400', label: 'Error' },
    summarizing: { icon: '📝', color: 'text-indigo-400', label: 'Summarizing' },
    charting: { icon: '📈', color: 'text-pink-400', label: 'Creating Chart' },
    complete: { icon: '✨', color: 'text-green-400', label: 'Complete' },
    done: { icon: '🎉', color: 'text-green-400', label: 'Done' },
    heartbeat: { icon: '💓', color: 'text-gray-500', label: 'Working' },
};

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
    steps,
    isLoading,
}) => {
    // Filter out heartbeats for display
    const visibleSteps = steps.filter(s => s.type !== 'heartbeat');

    if (visibleSteps.length === 0 && !isLoading) {
        return null;
    }

    const latestStep = visibleSteps[visibleSteps.length - 1];
    const isDone = latestStep?.type === 'done';

    return (
        <div className="mb-4 p-5 rounded-xl bg-gradient-to-br from-dark-800/80 to-dark-900/80 border border-primary-500/30 shadow-lg shadow-primary-500/10">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <div className={`w-4 h-4 rounded-full ${isDone ? 'bg-green-500' : 'bg-primary-500 animate-pulse'}`} />
                        {isLoading && !isDone && (
                            <div className="absolute inset-0 w-4 h-4 bg-primary-400 rounded-full animate-ping opacity-75" />
                        )}
                    </div>
                    <span className="text-base font-semibold text-white">
                        {isDone ? '✨ Agent Complete' : '🤖 Agent Working...'}
                    </span>
                </div>
                <span className="text-xs text-surface-400">
                    {visibleSteps.length} step{visibleSteps.length !== 1 ? 's' : ''}
                </span>
            </div>

            {/* Steps Timeline */}
            <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar pr-2">
                {visibleSteps.map((step, index) => {
                    const config = stepConfig[step.type] || { icon: '•', color: 'text-gray-400', label: step.type };
                    const isLatest = index === visibleSteps.length - 1;

                    return (
                        <div
                            key={index}
                            className={`flex items-start gap-3 p-3 rounded-lg transition-all duration-300 ${isLatest && !isDone
                                ? 'bg-primary-500/10 border border-primary-500/30'
                                : 'bg-dark-700/30'
                                }`}
                        >
                            {/* Step Icon */}
                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-dark-600 flex items-center justify-center text-lg">
                                {config.icon}
                            </div>

                            {/* Step Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className={`font-medium text-sm ${config.color}`}>
                                        {config.label}
                                    </span>
                                    <span className="text-xs text-surface-500">
                                        {new Date(step.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                                <p className="text-sm text-surface-300 mt-1 break-words">
                                    {step.description}
                                </p>

                                {/* Show SQL if available */}
                                {step.details?.sql && typeof step.details.sql === 'string' && (
                                    <details className="mt-2">
                                        <summary className="cursor-pointer text-xs text-primary-400 hover:text-primary-300 font-medium">
                                            📜 View Generated SQL
                                        </summary>
                                        <pre className="mt-2 p-3 bg-dark-900 rounded-lg text-xs text-green-400 overflow-x-auto font-mono border border-dark-600">
                                            {step.details.sql}
                                        </pre>
                                    </details>
                                )}

                                {/* Show row count if available */}
                                {step.details?.row_count !== undefined && (
                                    <div className="mt-2 text-xs text-surface-400">
                                        📊 Rows returned: <span className="text-green-400 font-medium">{Number(step.details.row_count)}</span>
                                    </div>
                                )}

                                {/* Show columns if available */}
                                {step.details?.columns && Array.isArray(step.details.columns) && (
                                    <div className="mt-1 text-xs text-surface-400">
                                        📋 Columns: <span className="text-cyan-400">{(step.details.columns as string[]).join(', ')}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}

                {/* Loading indicator for current step */}
                {isLoading && visibleSteps.length > 0 && !isDone && (
                    <div className="flex items-center gap-2 text-sm text-surface-400 px-3 py-2">
                        <div className="flex space-x-1">
                            <span className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </div>
                        <span>Processing...</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ThinkingIndicator;
