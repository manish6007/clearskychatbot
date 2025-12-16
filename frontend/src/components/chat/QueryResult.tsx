/** QueryResult component */

import { useState } from 'react';
import { Download, Clock, AlertCircle } from 'lucide-react';
import { Card, DataTable, CollapsibleSection, StatusBadge, Button } from '../common';
import { QuickChartPanel } from '../charts/QuickChartPanel';
import { ChartSelector } from '../charts/ChartSelector';
import { FeedbackButtons } from './FeedbackButtons';
import type { QueryResponse } from '../../types';

interface QueryResultProps {
    response: QueryResponse;
    sessionId?: string;
}

export function QueryResult({ response, sessionId }: QueryResultProps) {
    const [selectedChartId, setSelectedChartId] = useState<string | null>(
        response.quick_chart?.id || null
    );

    const allCharts = [
        ...(response.quick_chart ? [response.quick_chart] : []),
        ...(response.alternative_charts || []),
    ];

    const selectedChart = allCharts.find((c) => c.id === selectedChartId) || response.quick_chart;

    return (
        <div className="space-y-4">
            {/* Status and timing */}
            <div className="flex items-center gap-4">
                <StatusBadge status={response.status} />
                {response.execution_time_ms && (
                    <span className="flex items-center gap-1 text-sm text-surface-400">
                        <Clock className="h-4 w-4" />
                        {(response.execution_time_ms / 1000).toFixed(2)}s
                    </span>
                )}
            </div>

            {/* Error */}
            {response.error && (
                <Card className="bg-red-500/10 border border-red-500/30">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
                        <div>
                            <p className="font-medium text-red-400">{response.error.message}</p>
                            {response.error.details && (
                                <p className="text-sm text-red-300/70 mt-1">{response.error.details}</p>
                            )}
                        </div>
                    </div>
                </Card>
            )}

            {/* Summary */}
            {response.answer_summary && (
                <Card className="bg-surface-800/50">
                    <p className="text-surface-100 leading-relaxed">{response.answer_summary}</p>
                </Card>
            )}

            {/* Quick Chart */}
            {selectedChart && response.result_preview && (
                <div className="space-y-3">
                    {allCharts.length > 1 && (
                        <ChartSelector
                            charts={allCharts}
                            selectedId={selectedChartId}
                            onSelect={setSelectedChartId}
                        />
                    )}
                    <QuickChartPanel
                        chart={selectedChart}
                        data={response.result_preview}
                    />
                </div>
            )}

            {/* Data Table */}
            {response.result_preview && (
                <CollapsibleSection
                    title={`Data Preview (${response.result_preview.total_rows} rows)`}
                    defaultOpen={!selectedChart}
                >
                    <DataTable
                        columns={response.result_preview.columns}
                        rows={response.result_preview.rows}
                        maxRows={50}
                    />
                </CollapsibleSection>
            )}

            {/* SQL */}
            {response.sql && (
                <CollapsibleSection title="Generated SQL">
                    <pre className="bg-surface-900/50 rounded-lg p-4 overflow-x-auto text-sm text-surface-300 font-mono">
                        <code>{response.sql}</code>
                    </pre>
                    {response.sql_explanation && (
                        <div className="mt-3 text-sm text-surface-400">
                            {response.sql_explanation}
                        </div>
                    )}
                </CollapsibleSection>
            )}

            {/* Feedback */}
            {response.status === 'completed' && sessionId && (
                <div className="pt-2 border-t border-surface-700/50">
                    <FeedbackButtons
                        messageId={response.message_id}
                        sessionId={sessionId}
                    />
                </div>
            )}

            {/* Download link */}
            {response.s3_result_url && (
                <div className="flex justify-end">
                    <Button
                        as="a"
                        href={response.s3_result_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="secondary"
                        size="sm"
                    >
                        <Download className="h-4 w-4 mr-2" />
                        Download Full Results
                    </Button>
                </div>
            )}
        </div>
    );
}

export default QueryResult;
