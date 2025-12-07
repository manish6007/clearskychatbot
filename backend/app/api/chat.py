"""Chat API Endpoints - Query, updates, history management with SSE streaming."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import json
import asyncio

from app.models.chat import (
    QueryRequest, QueryResponse, UpdatesResponse,
    SessionListItem, ChatSession
)
from app.agents.text_to_sql_agent import (
    get_text_to_sql_agent, get_session, get_all_sessions,
    get_pending_response, delete_session, stream_agent_steps
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def process_query_background(request: QueryRequest, message_id: str):
    """Process query in background for streaming support."""
    agent = get_text_to_sql_agent()
    await agent.process_query(request, message_id)


@router.post("/query")
async def submit_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Submit a natural language question to be converted to SQL and executed.
    
    Returns immediately with a message_id. Connect to /stream/{message_id}
    to receive real-time updates, then poll /updates to get final results.
    """
    logger.info(f"Received query: {request.question[:100]}...")
    
    agent = get_text_to_sql_agent()
    
    # Generate IDs immediately
    import uuid
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    # Initialize response and queue before starting background task
    from app.agents.text_to_sql_agent import _streaming_queues, _pending_responses
    from datetime import datetime
    _streaming_queues[message_id] = asyncio.Queue(maxsize=100)
    
    initial_response = QueryResponse(
        session_id=session_id,
        message_id=message_id,
        status="running"
    )
    _pending_responses[message_id] = initial_response
    
    # Start processing in background
    background_tasks.add_task(
        agent.process_query_background,
        request,
        session_id,
        message_id
    )
    
    return initial_response


@router.get("/stream/{message_id}")
async def stream_thinking(message_id: str):
    """
    Stream agent thinking steps in real-time via Server-Sent Events (SSE).
    
    Connect to this endpoint IMMEDIATELY after submitting a query to see 
    the agent's reasoning process as it happens.
    """
    async def event_generator():
        try:
            # Wait a moment for the queue to be created
            await asyncio.sleep(0.1)
            
            async for step in stream_agent_steps(message_id):
                data = json.dumps(step)
                yield f"data: {data}\n\n"
                
                if step.get("type") == "done":
                    break
                    
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/updates", response_model=UpdatesResponse)
async def get_updates(session_id: str, message_id: str):
    """
    Poll for updates on a running query.
    
    Returns current status and partial results.
    """
    response = get_pending_response(message_id)
    
    if not response:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return UpdatesResponse(
        session_id=response.session_id,
        message_id=message_id,
        status=response.status,
        partial_summary=response.answer_summary,
        partial_sql=response.sql,
        current_step=None,
        progress_percent=(
            100 if response.status == "completed" 
            else 50 if response.sql else 25
        )
    )


@router.get("/result/{message_id}", response_model=QueryResponse)
async def get_result(message_id: str):
    """
    Get the final result of a query by message_id.
    Poll this after receiving 'done' from the stream.
    """
    response = get_pending_response(message_id)
    
    if not response:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return response


@router.get("/history", response_model=list[SessionListItem])
async def get_history(limit: int = 20, offset: int = 0):
    """
    Get list of chat sessions.
    """
    sessions = get_all_sessions()
    
    # Sort by updated_at descending
    sessions.sort(key=lambda s: s.updated_at, reverse=True)
    
    # Paginate
    paginated = sessions[offset:offset + limit]
    
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
async def get_session_details(session_id: str):
    """
    Get full session details including all messages.
    """
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str):
    """
    Delete a chat session.
    """
    success = delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted", "session_id": session_id}


@router.post("/session/{session_id}/continue", response_model=QueryResponse)
async def continue_session(session_id: str, request: QueryRequest):
    """
    Continue an existing chat session with a follow-up question.
    """
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Override session_id in request
    request.session_id = session_id
    
    agent = get_text_to_sql_agent()
    response = await agent.process_query(request)
    
    return response
