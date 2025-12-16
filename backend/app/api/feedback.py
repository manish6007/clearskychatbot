"""Feedback API Endpoints - Handle user feedback submission and statistics."""

import logging
from fastapi import APIRouter, HTTPException

from app.models.feedback import (
    FeedbackRequest, FeedbackResponse, FeedbackStats, PolicyHint
)
from app.services.policy_engine import get_policy_engine
from app.agents.text_to_sql_agent import get_pending_response, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback (👍/👎) for a query response.
    
    This feedback is used to improve future SQL generation through policy evolution.
    """
    logger.info(
        f"Received feedback: {request.feedback_type.value} for message {request.message_id}"
    )
    
    # Get the original response to extract question and SQL
    response = get_pending_response(request.message_id)
    if not response:
        raise HTTPException(
            status_code=404,
            detail=f"Message {request.message_id} not found"
        )
    
    # Get the question from the session
    session = get_session(request.session_id)
    question = ""
    if session:
        # Find the user message before this response
        for msg in session.messages:
            if msg.role == "user":
                question = msg.content
            elif msg.response and msg.response.message_id == request.message_id:
                break
    
    if not question:
        # Fallback: use a placeholder
        question = "Unknown question"
        logger.warning(f"Could not find question for message {request.message_id}")
    
    sql = response.sql or ""
    
    # Record the feedback
    policy_engine = get_policy_engine()
    record = policy_engine.record_feedback(
        message_id=request.message_id,
        session_id=request.session_id,
        question=question,
        sql=sql,
        feedback_type=request.feedback_type,
        reason=request.reason
    )
    
    return FeedbackResponse(
        success=True,
        feedback_id=record.id,
        message=f"Thank you for your feedback! This helps improve future responses."
    )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """
    Get aggregated feedback statistics.
    
    Returns success rates, feedback counts by table, and active policy hints.
    """
    policy_engine = get_policy_engine()
    stats = policy_engine.get_feedback_stats()
    
    return stats


@router.get("/policy-hints", response_model=list[PolicyHint])
async def get_current_policy_hints():
    """
    Get current active policy hints.
    
    Useful for debugging and transparency into what the system has learned.
    """
    from app.services.rlhf_store import get_rlhf_store
    
    store = get_rlhf_store()
    state = store.get_policy_state()
    
    return state.hints


@router.post("/analyze")
async def trigger_policy_analysis():
    """
    Manually trigger a full policy analysis.
    
    This recalculates all policy hints from the accumulated feedback.
    """
    policy_engine = get_policy_engine()
    hints_count = policy_engine.analyze_and_update_policies()
    
    return {
        "success": True,
        "message": f"Policy analysis complete. {hints_count} hints created/updated."
    }


@router.delete("/clear")
async def clear_all_feedback():
    """
    Clear all feedback data (for testing/reset purposes).
    
    WARNING: This permanently deletes all feedback and learned policies.
    """
    from app.services.rlhf_store import get_rlhf_store
    
    store = get_rlhf_store()
    store.clear_all_data()
    
    logger.warning("All RLHF data has been cleared")
    
    return {
        "success": True,
        "message": "All feedback and policy data has been cleared."
    }
