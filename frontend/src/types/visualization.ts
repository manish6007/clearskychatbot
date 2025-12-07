/** Visualization types matching backend ChartConfig */

export type ChartType =
    | 'bar'
    | 'line'
    | 'pie'
    | 'scatter'
    | 'area'
    | 'bubble'
    | 'heatmap'
    | 'scatter3d'
    | 'surface3d'
    | 'table';

export interface ChartEncoding {
    xField?: string;
    yField?: string;
    zField?: string;
    seriesField?: string;
    sizeField?: string;
    colorField?: string;
    valueField?: string;
    labelField?: string;
}

export interface ChartConfig {
    id: string;
    title?: string;
    type: ChartType;
    encoding: ChartEncoding;
    spec?: Record<string, unknown>;
    is_quick_recommendation: boolean;
    rationale?: string;
}

export interface PlotlyLayoutConfig {
    title?: string;
    xaxis?: {
        title?: string;
        type?: string;
    };
    yaxis?: {
        title?: string;
        type?: string;
    };
    zaxis?: {
        title?: string;
    };
    showlegend?: boolean;
    legend?: {
        x?: number;
        y?: number;
    };
    paper_bgcolor?: string;
    plot_bgcolor?: string;
    font?: {
        color?: string;
        family?: string;
    };
    margin?: {
        l?: number;
        r?: number;
        t?: number;
        b?: number;
    };
}
