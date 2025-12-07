"""Visualization models for chart configuration."""

from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


ChartType = Literal[
    "bar",
    "line",
    "pie",
    "scatter",
    "area",
    "bubble",
    "heatmap",
    "scatter3d",
    "surface3d",
    "table"
]


class ChartEncoding(BaseModel):
    """Field mappings for chart visualization."""
    xField: Optional[str] = Field(default=None, description="X-axis field")
    yField: Optional[str] = Field(default=None, description="Y-axis field")
    zField: Optional[str] = Field(default=None, description="Z-axis field for 3D charts")
    seriesField: Optional[str] = Field(default=None, description="Field for grouping/series")
    sizeField: Optional[str] = Field(default=None, description="Field for bubble size")
    colorField: Optional[str] = Field(default=None, description="Field for color encoding")
    valueField: Optional[str] = Field(default=None, description="Field for heatmap/matrix value")
    labelField: Optional[str] = Field(default=None, description="Field for labels")


class ChartConfig(BaseModel):
    """Configuration for a chart visualization."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = Field(default=None, description="Chart title")
    type: ChartType = Field(..., description="Chart type")
    encoding: ChartEncoding = Field(default_factory=ChartEncoding)
    spec: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full Plotly spec override if needed"
    )
    is_quick_recommendation: bool = Field(
        default=False,
        description="True for the primary Quick Chart recommendation"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Short explanation of why this chart type was recommended"
    )


class ChartRecommendation(BaseModel):
    """Chart recommendation result from the agent."""
    quick_chart: Optional[ChartConfig] = Field(
        default=None,
        description="Primary recommended chart"
    )
    alternative_charts: List[ChartConfig] = Field(
        default_factory=list,
        description="Alternative chart options"
    )


class DataAnalysis(BaseModel):
    """Analysis of query result data for chart selection."""
    row_count: int = Field(..., description="Number of rows")
    column_count: int = Field(..., description="Number of columns")
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    datetime_columns: List[str] = Field(default_factory=list)
    has_aggregation: bool = Field(default=False)
    has_time_series: bool = Field(default=False)
    has_multiple_series: bool = Field(default=False)
    cardinality: Dict[str, int] = Field(default_factory=dict)
