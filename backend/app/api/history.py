"""History API Endpoints - Session history management."""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
import logging

from app.models.chat import SessionListItem, ChatSession
from app.agents.text_to_sql_agent import (
    get_all_sessions, get_session, delete_session
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/sessions", response_model=List[SessionListItem])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    days: int = 30
):
    """
    List chat sessions from the last N days.
    """
    sessions = get_all_sessions()
    
    # Filter by date
    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = [s for s in sessions if s.created_at >= cutoff]
    
    # Sort by updated_at descending
    filtered.sort(key=lambda s: s.updated_at, reverse=True)
    
    # Paginate
    paginated = filtered[offset:offset + limit]
    
    # Convert to list items
    items = []
    for session in paginated:
        user_messages = [m for m in session.messages if m.role == "user"]
        items.append(SessionListItem(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(session.messages),
            last_question=user_messages[-1].content if user_messages else None
        ))
    
    return items


@router.get("/session/{session_id}", response_model=ChatSession)
async def get_session_history(session_id: str):
    """
    Get full conversation history for a session.
    """
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.delete("/session/{session_id}")
async def delete_session_history(session_id: str):
    """
    Delete a session and its history.
    """
    success = delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}


@router.delete("/sessions/clear")
async def clear_old_sessions(days: int = 30):
    """
    Clear sessions older than specified days.
    """
    sessions = get_all_sessions()
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    deleted_count = 0
    for session in sessions:
        if session.updated_at < cutoff:
            delete_session(session.id)
            deleted_count += 1
    
    return {
        "message": f"Cleared {deleted_count} old sessions",
        "deleted_count": deleted_count
    }


@router.get("/stats")
async def get_history_stats():
    """
    Get statistics about chat history.
    """
    sessions = get_all_sessions()
    
    total_sessions = len(sessions)
    total_messages = sum(len(s.messages) for s in sessions)
    
    # Sessions in last 24 hours
    day_ago = datetime.utcnow() - timedelta(days=1)
    recent_sessions = len([s for s in sessions if s.created_at >= day_ago])
    
    # Sessions in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_sessions = len([s for s in sessions if s.created_at >= week_ago])
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "sessions_last_24h": recent_sessions,
        "sessions_last_7d": weekly_sessions,
        "avg_messages_per_session": (
            total_messages / total_sessions if total_sessions > 0 else 0
        )
    }
