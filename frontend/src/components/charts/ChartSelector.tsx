/** ChartSelector - Select between chart options */

import {
    BarChart3, LineChart, PieChart, ScatterChart,
    Activity, Circle, Grid3X3, Box, Layers, Table2
} from 'lucide-react';
import clsx from 'clsx';
import type { ChartConfig, ChartType } from '../../types';

interface ChartSelectorProps {
    charts: ChartConfig[];
    selectedId: string | null;
    onSelect: (id: string) => void;
}

const chartIcons: Record<ChartType, React.ComponentType<{ className?: string }>> = {
    bar: BarChart3,
    line: LineChart,
    pie: PieChart,
    scatter: ScatterChart,
    area: Activity,
    bubble: Circle,
    heatmap: Grid3X3,
    scatter3d: Box,
    surface3d: Layers,
    table: Table2,
};

const chartLabels: Record<ChartType, string> = {
    bar: 'Bar',
    line: 'Line',
    pie: 'Pie',
    scatter: 'Scatter',
    area: 'Area',
    bubble: 'Bubble',
    heatmap: 'Heatmap',
    scatter3d: '3D Scatter',
    surface3d: '3D Surface',
    table: 'Table',
};

export function ChartSelector({ charts, selectedId, onSelect }: ChartSelectorProps) {
    return (
        <div className="flex flex-wrap gap-2">
            {charts.map((chart) => {
                const Icon = chartIcons[chart.type] || BarChart3;
                const isSelected = chart.id === selectedId;
                const isQuick = chart.is_quick_recommendation;

                return (
                    <button
                        key={chart.id}
                        onClick={() => onSelect(chart.id)}
                        className={clsx(
                            'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-smooth',
                            isSelected
                                ? 'bg-primary-500/30 text-primary-300 border border-primary-500/50'
                                : 'bg-surface-800/50 text-surface-400 border border-surface-700 hover:bg-surface-700/50 hover:text-surface-200'
                        )}
                    >
                        <Icon className="h-4 w-4" />
                        <span>{chartLabels[chart.type]}</span>
                        {isQuick && (
                            <span className="px-1.5 py-0.5 text-xs rounded bg-primary-500/30 text-primary-300">
                                Recommended
                            </span>
                        )}
                    </button>
                );
            })}
        </div>
    );
}

export default ChartSelector;
