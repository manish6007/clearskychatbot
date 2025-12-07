/** QuickChartPanel - Primary chart recommendation display */

import { Lightbulb } from 'lucide-react';
import { Card } from '../common';
import { ChartRenderer } from './ChartRenderer';
import type { ChartConfig, ResultPreview } from '../../types';

interface QuickChartPanelProps {
    chart: ChartConfig;
    data: ResultPreview;
}

export function QuickChartPanel({ chart, data }: QuickChartPanelProps) {
    return (
        <Card variant="elevated" padding="none" className="overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-primary-500/20 to-accent-500/20 border-b border-surface-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-primary-500/30 flex items-center justify-center">
                        <Lightbulb className="h-4 w-4 text-primary-400" />
                    </div>
                    <div>
                        <h3 className="font-medium text-surface-100">
                            {chart.is_quick_recommendation ? 'Quick Chart' : chart.title || 'Visualization'}
                        </h3>
                        <p className="text-xs text-surface-400 capitalize">{chart.type.replace('3d', ' 3D')}</p>
                    </div>
                </div>
            </div>

            {/* Chart */}
            <div className="p-4">
                <ChartRenderer chart={chart} data={data} />
            </div>

            {/* Rationale */}
            {chart.rationale && (
                <div className="px-4 py-3 bg-surface-800/30 border-t border-surface-700">
                    <p className="text-sm text-surface-400">
                        <span className="text-surface-500 font-medium">Why this chart: </span>
                        {chart.rationale}
                    </p>
                </div>
            )}
        </Card>
    );
}

export default QuickChartPanel;
