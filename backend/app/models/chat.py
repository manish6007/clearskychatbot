"""Chat models for API requests and responses."""

from typing import Optional, List, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .visualization import ChartConfig


class QueryOptions(BaseModel):
    """Options for a query request."""
    max_rows: Optional[int] = Field(default=None, description="Maximum rows to return")
    catalog: Optional[str] = Field(default=None, description="Override data catalog")
    database: Optional[str] = Field(default=None, description="Override database")
    environment: Optional[Literal["UAT", "PROD"]] = Field(
        default="PROD",
        description="Environment to query"
    )
    debug: bool = Field(default=False, description="Enable debug output")
    explain_sql: bool = Field(default=False, description="Include SQL explanation")
    visualization_mode: Literal["auto", "table_only", "chart_only"] = Field(
        default="auto",
        description="Visualization mode"
    )
    allow_advanced_charts: bool = Field(default=True, description="Allow advanced chart types")


class QueryRequest(BaseModel):
    """Request body for chat query endpoint."""
    session_id: Optional[str] = Field(default=None, description="Existing session ID")
    question: str = Field(..., min_length=1, description="Natural language question")
    options: QueryOptions = Field(default_factory=QueryOptions)


class ResultPreview(BaseModel):
    """Preview of query results."""
    columns: List[str] = Field(..., description="Column names")
    rows: List[List[Any]] = Field(..., description="Data rows")
    total_rows: int = Field(..., description="Total number of rows in full result")
    truncated: bool = Field(default=False, description="Whether result was truncated")


class AgentStep(BaseModel):
    """An intermediate step from the agent."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_type: str = Field(..., description="Type of step (e.g., 'retrieval', 'sql_generation')")
    description: str = Field(..., description="Description of what happened")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[dict] = Field(default=None, description="Additional step details")


class QueryError(BaseModel):
    """Error information for failed queries."""
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Error details")
    error_type: Optional[str] = Field(default=None, description="Error type/category")


class QueryResponse(BaseModel):
    """Response from chat query endpoint."""
    session_id: str = Field(..., description="Session ID")
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["running", "completed", "failed"] = Field(
        default="running",
        description="Query status"
    )
    answer_summary: Optional[str] = Field(default=None, description="Natural language summary")
    sql: Optional[str] = Field(default=None, description="Generated SQL query")
    sql_explanation: Optional[str] = Field(default=None, description="Explanation of generated SQL")
    result_preview: Optional[ResultPreview] = Field(default=None, description="Result preview")
    quick_chart: Optional[ChartConfig] = Field(
        default=None,
        description="Primary recommended chart"
    )
    alternative_charts: Optional[List[ChartConfig]] = Field(
        default=None,
        description="Other suggested chart options"
    )
    s3_result_url: Optional[str] = Field(default=None, description="S3 URL for large results")
    intermediate_steps: Optional[List[AgentStep]] = Field(
        default=None,
        description="Agent intermediate steps"
    )
    error: Optional[QueryError] = Field(default=None, description="Error information if failed")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time in ms")


class ChatMessage(BaseModel):
    """A message in a chat session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response: Optional[QueryResponse] = Field(
        default=None,
        description="Full response for assistant messages"
    )


class ChatSession(BaseModel):
    """A chat session with conversation history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = Field(default=None, description="Session title")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[ChatMessage] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SessionListItem(BaseModel):
    """Summary of a session for listing."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_question: Optional[str]


class UpdatesResponse(BaseModel):
    """Response for polling updates endpoint."""
    session_id: str
    message_id: str
    status: Literal["running", "completed", "failed"]
    partial_summary: Optional[str] = None
    partial_sql: Optional[str] = None
    current_step: Optional[str] = None
    progress_percent: Optional[int] = None
