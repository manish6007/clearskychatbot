/** ChartRenderer - Plotly chart rendering */

import Plot from 'react-plotly.js';
import type { ChartConfig, ResultPreview } from '../../types';

interface ChartRendererProps {
    chart: ChartConfig;
    data: ResultPreview;
    height?: number;
}

const darkTheme = {
    paper_bgcolor: 'rgba(15, 23, 42, 0.8)',
    plot_bgcolor: 'rgba(15, 23, 42, 0.8)',
    font: {
        color: '#e2e8f0',
        family: 'Inter, system-ui, sans-serif',
    },
    xaxis: {
        gridcolor: 'rgba(71, 85, 105, 0.3)',
        linecolor: 'rgba(71, 85, 105, 0.5)',
        zerolinecolor: 'rgba(71, 85, 105, 0.5)',
    },
    yaxis: {
        gridcolor: 'rgba(71, 85, 105, 0.3)',
        linecolor: 'rgba(71, 85, 105, 0.5)',
        zerolinecolor: 'rgba(71, 85, 105, 0.5)',
    },
    colorway: ['#0ea5e9', '#8b5cf6', '#f59e0b', '#22c55e', '#ef4444', '#ec4899', '#06b6d4', '#84cc16'],
};

function getColumnData(data: ResultPreview, fieldName?: string): unknown[] {
    if (!fieldName) return [];
    const colIndex = data.columns.indexOf(fieldName);
    if (colIndex === -1) return [];
    return data.rows.map((row) => row[colIndex]);
}

function buildPlotData(chart: ChartConfig, data: ResultPreview): Plotly.Data[] {
    const { type, encoding } = chart;

    switch (type) {
        case 'bar':
            return [{
                type: 'bar',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                marker: { color: '#0ea5e9' },
            }];

        case 'line':
            return [{
                type: 'scatter',
                mode: 'lines+markers',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                line: { color: '#0ea5e9', width: 2 },
                marker: { size: 6 },
            }];

        case 'scatter':
            return [{
                type: 'scatter',
                mode: 'markers',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                marker: {
                    color: encoding.colorField
                        ? getColumnData(data, encoding.colorField)
                        : '#0ea5e9',
                    size: 10,
                    colorscale: 'Viridis',
                    showscale: !!encoding.colorField,
                },
            }];

        case 'pie':
            return [{
                type: 'pie',
                labels: getColumnData(data, encoding.labelField),
                values: getColumnData(data, encoding.valueField),
                hole: 0.4,
                textinfo: 'label+percent',
                textfont: { color: '#fff' },
            }];

        case 'area':
            return [{
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                line: { color: '#0ea5e9' },
                fillcolor: 'rgba(14, 165, 233, 0.3)',
            }];

        case 'bubble':
            const sizeData = getColumnData(data, encoding.sizeField) as number[];
            const maxSize = Math.max(...sizeData.filter((v) => typeof v === 'number'));
            const normalizedSize = sizeData.map((v) =>
                typeof v === 'number' ? (v / maxSize) * 50 + 10 : 20
            );

            return [{
                type: 'scatter',
                mode: 'markers',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                marker: {
                    size: normalizedSize,
                    color: encoding.colorField
                        ? getColumnData(data, encoding.colorField)
                        : '#0ea5e9',
                    colorscale: 'Viridis',
                    showscale: !!encoding.colorField,
                    opacity: 0.7,
                },
                text: encoding.labelField ? getColumnData(data, encoding.labelField) : undefined,
            }];

        case 'heatmap':
            return [{
                type: 'heatmap',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                z: getColumnData(data, encoding.valueField),
                colorscale: 'Viridis',
            }];

        case 'scatter3d':
            return [{
                type: 'scatter3d',
                mode: 'markers',
                x: getColumnData(data, encoding.xField),
                y: getColumnData(data, encoding.yField),
                z: getColumnData(data, encoding.zField),
                marker: {
                    size: 6,
                    color: encoding.colorField
                        ? getColumnData(data, encoding.colorField)
                        : '#0ea5e9',
                    colorscale: 'Viridis',
                    showscale: !!encoding.colorField,
                },
            }];

        case 'surface3d':
            // Surface requires z to be a 2D array
            const xVals = [...new Set(getColumnData(data, encoding.xField) as string[])];
            const yVals = [...new Set(getColumnData(data, encoding.yField) as string[])];
            const zValues = getColumnData(data, encoding.zField) as number[];

            const zMatrix: number[][] = [];
            let idx = 0;
            for (let i = 0; i < yVals.length; i++) {
                zMatrix.push([]);
                for (let j = 0; j < xVals.length; j++) {
                    zMatrix[i].push(zValues[idx] || 0);
                    idx++;
                }
            }

            return [{
                type: 'surface',
                x: xVals,
                y: yVals,
                z: zMatrix,
                colorscale: 'Viridis',
            }];

        default:
            return [];
    }
}

function buildLayout(chart: ChartConfig, height: number): Partial<Plotly.Layout> {
    const { type, encoding, title } = chart;

    const baseLayout: Partial<Plotly.Layout> = {
        ...darkTheme,
        title: title ? { text: title, font: { size: 16 } } : undefined,
        height,
        margin: { l: 60, r: 30, t: title ? 50 : 30, b: 50 },
        showlegend: false,
        autosize: true,
    };

    if (type === 'scatter3d' || type === 'surface3d') {
        return {
            ...baseLayout,
            scene: {
                xaxis: { title: encoding.xField, ...darkTheme.xaxis },
                yaxis: { title: encoding.yField, ...darkTheme.yaxis },
                zaxis: { title: encoding.zField, gridcolor: 'rgba(71, 85, 105, 0.3)' },
                bgcolor: 'rgba(15, 23, 42, 0.8)',
            },
        };
    }

    return {
        ...baseLayout,
        xaxis: {
            ...darkTheme.xaxis,
            title: encoding.xField,
        },
        yaxis: {
            ...darkTheme.yaxis,
            title: encoding.yField,
        },
    };
}

export function ChartRenderer({ chart, data, height = 400 }: ChartRendererProps) {
    if (chart.type === 'table') {
        return null; // Tables are handled separately
    }

    const plotData = buildPlotData(chart, data);
    const layout = buildLayout(chart, height);

    return (
        <div className="w-full rounded-lg overflow-hidden">
            <Plot
                data={plotData}
                layout={layout}
                config={{
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                }}
                style={{ width: '100%', height: `${height}px` }}
                useResizeHandler
            />
        </div>
    );
}

export default ChartRenderer;
