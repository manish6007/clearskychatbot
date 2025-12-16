"""Feedback models for RLHF implementation."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class FeedbackType(str, Enum):
    """Type of user feedback."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class FeedbackRecord(BaseModel):
    """A single feedback record from a user interaction."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = Field(..., description="ID of the message being rated")
    session_id: str = Field(..., description="Session ID")
    question: str = Field(..., description="Original user question")
    sql: str = Field(..., description="Generated SQL query")
    feedback_type: FeedbackType = Field(..., description="User feedback type")
    reason: Optional[str] = Field(default=None, description="Optional reason for feedback")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (tables, patterns, etc.)"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FeedbackRequest(BaseModel):
    """Request body for submitting feedback."""
    message_id: str = Field(..., description="Message ID to rate")
    session_id: str = Field(..., description="Session ID")
    feedback_type: FeedbackType = Field(..., description="Thumbs up or down")
    reason: Optional[str] = Field(default=None, description="Optional reason")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    success: bool
    feedback_id: str
    message: str


class PolicyHint(BaseModel):
    """A learned policy hint to improve SQL generation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hint_type: str = Field(..., description="Type: prefer, avoid, pattern, tip")
    description: str = Field(..., description="Human-readable hint description")
    weight: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0,
        description="Importance weight (0.0-1.0)"
    )
    tables: List[str] = Field(default_factory=list, description="Related tables")
    pattern: Optional[str] = Field(default=None, description="SQL pattern if applicable")
    source_feedback_count: int = Field(
        default=1, 
        description="Number of feedback records supporting this hint"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackStats(BaseModel):
    """Aggregated feedback statistics."""
    total_feedback: int = 0
    thumbs_up_count: int = 0
    thumbs_down_count: int = 0
    success_rate: float = 0.0
    feedback_by_table: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    recent_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    active_hints: int = 0


class PolicyState(BaseModel):
    """Current state of all learned policies."""
    hints: List[PolicyHint] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
