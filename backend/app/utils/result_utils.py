"""Result Utilities - Processing and analysis of query results."""

import logging
from typing import List, Any, Dict, Optional
from datetime import datetime, date
import re

from app.models.chat import ResultPreview
from app.models.visualization import (
    DataAnalysis, ChartConfig, ChartEncoding, ChartRecommendation
)

logger = logging.getLogger(__name__)


def analyze_result_data(result: ResultPreview) -> DataAnalysis:
    """
    Analyze query result data to determine appropriate visualizations.
    """
    columns = result.columns
    rows = result.rows
    
    numeric_columns = []
    categorical_columns = []
    datetime_columns = []
    cardinality = {}
    
    for i, col in enumerate(columns):
        col_values = [row[i] for row in rows if row[i] is not None]
        
        if not col_values:
            continue
        
        # Determine column type
        col_type = infer_column_type(col_values, col)
        
        if col_type == "numeric":
            numeric_columns.append(col)
        elif col_type == "datetime":
            datetime_columns.append(col)
        else:
            categorical_columns.append(col)
        
        # Calculate cardinality
        cardinality[col] = len(set(str(v) for v in col_values))
    
    # Detect patterns
    has_time_series = len(datetime_columns) > 0 and len(numeric_columns) > 0
    has_aggregation = any(
        agg in col.lower() 
        for col in columns 
        for agg in ["sum", "count", "avg", "min", "max", "total"]
    )
    has_multiple_series = (
        len(categorical_columns) > 0 and 
        len(numeric_columns) > 0 and
        any(cardinality.get(c, 0) > 1 for c in categorical_columns)
    )
    
    return DataAnalysis(
        row_count=len(rows),
        column_count=len(columns),
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        datetime_columns=datetime_columns,
        has_aggregation=has_aggregation,
        has_time_series=has_time_series,
        has_multiple_series=has_multiple_series,
        cardinality=cardinality
    )


def infer_column_type(values: List[Any], column_name: str) -> str:
    """
    Infer column type from sample values and column name.
    """
    # Check column name hints
    datetime_hints = ["date", "time", "created", "updated", "timestamp"]
    if any(hint in column_name.lower() for hint in datetime_hints):
        return "datetime"
    
    # Sample non-null values
    sample = values[:100]
    
    numeric_count = 0
    datetime_count = 0
    
    for val in sample:
        if val is None:
            continue
        
        val_str = str(val)
        
        # Check numeric
        try:
            float(val_str.replace(",", ""))
            numeric_count += 1
            continue
        except ValueError:
            pass
        
        # Check datetime patterns
        datetime_patterns = [
            r"\d{4}-\d{2}-\d{2}",
            r"\d{2}/\d{2}/\d{4}",
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
        ]
        if any(re.match(p, val_str) for p in datetime_patterns):
            datetime_count += 1
            continue
    
    total = len(sample)
    if total == 0:
        return "categorical"
    
    if datetime_count / total > 0.8:
        return "datetime"
    if numeric_count / total > 0.8:
        return "numeric"
    
    return "categorical"


def recommend_charts(
    result: ResultPreview,
    question: str,
    allow_advanced: bool = True
) -> ChartRecommendation:
    """
    Recommend chart types based on data analysis and question semantics.
    """
    analysis = analyze_result_data(result)
    
    # Check if data is suitable for visualization
    if analysis.row_count == 0:
        return ChartRecommendation(quick_chart=None, alternative_charts=[])
    
    # Analyze question for chart hints
    question_lower = question.lower()
    
    # Explicit chart type requests
    if "pie" in question_lower:
        quick = create_pie_chart(result, analysis)
    elif "bubble" in question_lower and allow_advanced:
        quick = create_bubble_chart(result, analysis)
    elif "heatmap" in question_lower and allow_advanced:
        quick = create_heatmap_chart(result, analysis)
    elif "3d" in question_lower or "surface" in question_lower:
        if allow_advanced:
            quick = create_surface3d_chart(result, analysis)
        else:
            quick = create_scatter_chart(result, analysis)
    elif "scatter" in question_lower:
        if "3d" in question_lower and allow_advanced:
            quick = create_scatter3d_chart(result, analysis)
        else:
            quick = create_scatter_chart(result, analysis)
    elif "trend" in question_lower or "over time" in question_lower:
        quick = create_line_chart(result, analysis)
    elif "top" in question_lower or "ranking" in question_lower:
        quick = create_bar_chart(result, analysis)
    elif "distribution" in question_lower or "breakdown" in question_lower:
        if analysis.row_count <= 10:
            quick = create_pie_chart(result, analysis)
        else:
            quick = create_bar_chart(result, analysis)
    else:
        # Auto-detect best chart
        quick = auto_select_chart(result, analysis, allow_advanced)
    
    if quick:
        quick.is_quick_recommendation = True
    
    # Generate alternatives
    alternatives = generate_alternative_charts(result, analysis, quick, allow_advanced)
    
    return ChartRecommendation(
        quick_chart=quick,
        alternative_charts=alternatives
    )


def auto_select_chart(
    result: ResultPreview,
    analysis: DataAnalysis,
    allow_advanced: bool
) -> Optional[ChartConfig]:
    """
    Automatically select the best chart type based on data characteristics.
    """
    # Time series data -> Line chart
    if analysis.has_time_series:
        return create_line_chart(result, analysis)
    
    # Few rows with categorical + numeric -> Bar or Pie
    if analysis.row_count <= 10:
        if len(analysis.numeric_columns) == 1:
            return create_pie_chart(result, analysis)
        return create_bar_chart(result, analysis)
    
    # Many categories -> Bar chart
    if len(analysis.categorical_columns) > 0 and len(analysis.numeric_columns) > 0:
        return create_bar_chart(result, analysis)
    
    # Multiple numeric columns -> Scatter
    if len(analysis.numeric_columns) >= 2:
        return create_scatter_chart(result, analysis)
    
    # Default to table
    return create_table_chart(result, analysis)


def create_bar_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create bar chart configuration."""
    x_field = (
        analysis.categorical_columns[0] 
        if analysis.categorical_columns 
        else result.columns[0]
    )
    y_field = (
        analysis.numeric_columns[0] 
        if analysis.numeric_columns 
        else result.columns[1] if len(result.columns) > 1 else result.columns[0]
    )
    
    series_field = (
        analysis.categorical_columns[1] 
        if len(analysis.categorical_columns) > 1 
        else None
    )
    
    return ChartConfig(
        title="Bar Chart",
        type="bar",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            seriesField=series_field
        ),
        rationale="Bar charts are effective for comparing values across categories."
    )


def create_line_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create line chart configuration."""
    x_field = (
        analysis.datetime_columns[0] 
        if analysis.datetime_columns 
        else analysis.categorical_columns[0] if analysis.categorical_columns
        else result.columns[0]
    )
    y_field = (
        analysis.numeric_columns[0] 
        if analysis.numeric_columns 
        else result.columns[1] if len(result.columns) > 1 else result.columns[0]
    )
    
    series_field = None
    if analysis.has_multiple_series and len(analysis.categorical_columns) > 0:
        series_field = analysis.categorical_columns[0]
    
    return ChartConfig(
        title="Line Chart",
        type="line",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            seriesField=series_field
        ),
        rationale="Line charts are ideal for showing trends over time or sequences."
    )


def create_pie_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create pie chart configuration."""
    label_field = (
        analysis.categorical_columns[0] 
        if analysis.categorical_columns 
        else result.columns[0]
    )
    value_field = (
        analysis.numeric_columns[0] 
        if analysis.numeric_columns 
        else result.columns[1] if len(result.columns) > 1 else result.columns[0]
    )
    
    return ChartConfig(
        title="Pie Chart",
        type="pie",
        encoding=ChartEncoding(
            labelField=label_field,
            valueField=value_field
        ),
        rationale="Pie charts show proportional breakdown of a whole."
    )


def create_scatter_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create scatter chart configuration."""
    x_field = (
        analysis.numeric_columns[0] 
        if analysis.numeric_columns 
        else result.columns[0]
    )
    y_field = (
        analysis.numeric_columns[1] 
        if len(analysis.numeric_columns) > 1 
        else analysis.numeric_columns[0] if analysis.numeric_columns
        else result.columns[1] if len(result.columns) > 1 else result.columns[0]
    )
    
    color_field = (
        analysis.categorical_columns[0] 
        if analysis.categorical_columns 
        else None
    )
    
    return ChartConfig(
        title="Scatter Plot",
        type="scatter",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            colorField=color_field
        ),
        rationale="Scatter plots reveal relationships between two numeric variables."
    )


def create_bubble_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create bubble chart configuration."""
    x_field = analysis.numeric_columns[0] if analysis.numeric_columns else result.columns[0]
    y_field = (
        analysis.numeric_columns[1] 
        if len(analysis.numeric_columns) > 1 
        else result.columns[1] if len(result.columns) > 1 else result.columns[0]
    )
    size_field = (
        analysis.numeric_columns[2] 
        if len(analysis.numeric_columns) > 2 
        else y_field
    )
    color_field = (
        analysis.categorical_columns[0] 
        if analysis.categorical_columns 
        else None
    )
    
    return ChartConfig(
        title="Bubble Chart",
        type="bubble",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            sizeField=size_field,
            colorField=color_field
        ),
        rationale="Bubble charts encode three dimensions using position and size."
    )


def create_heatmap_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create heatmap configuration."""
    x_field = (
        analysis.categorical_columns[0] 
        if analysis.categorical_columns 
        else result.columns[0]
    )
    y_field = (
        analysis.categorical_columns[1] 
        if len(analysis.categorical_columns) > 1 
        else result.columns[1] if len(result.columns) > 1 else result.columns[0]
    )
    value_field = (
        analysis.numeric_columns[0] 
        if analysis.numeric_columns 
        else result.columns[2] if len(result.columns) > 2 else result.columns[0]
    )
    
    return ChartConfig(
        title="Heatmap",
        type="heatmap",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            valueField=value_field
        ),
        rationale="Heatmaps visualize magnitude across two categorical dimensions."
    )


def create_scatter3d_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create 3D scatter chart configuration."""
    x_field = analysis.numeric_columns[0] if analysis.numeric_columns else result.columns[0]
    y_field = (
        analysis.numeric_columns[1] 
        if len(analysis.numeric_columns) > 1 
        else result.columns[1]
    )
    z_field = (
        analysis.numeric_columns[2] 
        if len(analysis.numeric_columns) > 2 
        else result.columns[2] if len(result.columns) > 2 else y_field
    )
    
    return ChartConfig(
        title="3D Scatter Plot",
        type="scatter3d",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            zField=z_field,
            colorField=analysis.categorical_columns[0] if analysis.categorical_columns else None
        ),
        rationale="3D scatter plots show relationships across three numeric dimensions."
    )


def create_surface3d_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create 3D surface chart configuration."""
    x_field = result.columns[0]
    y_field = result.columns[1] if len(result.columns) > 1 else result.columns[0]
    z_field = (
        analysis.numeric_columns[0] 
        if analysis.numeric_columns 
        else result.columns[2] if len(result.columns) > 2 else result.columns[0]
    )
    
    return ChartConfig(
        title="3D Surface Plot",
        type="surface3d",
        encoding=ChartEncoding(
            xField=x_field,
            yField=y_field,
            zField=z_field
        ),
        rationale="Surface plots visualize continuous 3D data as a mesh."
    )


def create_table_chart(result: ResultPreview, analysis: DataAnalysis) -> ChartConfig:
    """Create table configuration."""
    return ChartConfig(
        title="Data Table",
        type="table",
        encoding=ChartEncoding(),
        rationale="Tables are best for detailed data inspection and complex datasets."
    )


def generate_alternative_charts(
    result: ResultPreview,
    analysis: DataAnalysis,
    quick_chart: Optional[ChartConfig],
    allow_advanced: bool
) -> List[ChartConfig]:
    """Generate alternative chart options."""
    alternatives = []
    quick_type = quick_chart.type if quick_chart else None
    
    chart_generators = [
        ("bar", create_bar_chart),
        ("line", create_line_chart),
        ("scatter", create_scatter_chart),
        ("pie", create_pie_chart),
        ("table", create_table_chart),
    ]
    
    if allow_advanced:
        chart_generators.extend([
            ("bubble", create_bubble_chart),
            ("heatmap", create_heatmap_chart),
            ("scatter3d", create_scatter3d_chart),
        ])
    
    for chart_type, generator in chart_generators:
        if chart_type != quick_type:
            try:
                chart = generator(result, analysis)
                chart.is_quick_recommendation = False
                alternatives.append(chart)
            except Exception as e:
                logger.debug(f"Could not create {chart_type} chart: {e}")
                continue
    
    return alternatives[:5]  # Limit to 5 alternatives
