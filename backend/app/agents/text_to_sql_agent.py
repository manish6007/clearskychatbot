"""Text-to-SQL Agent - Orchestrated agent with self-correction, streaming, and session memory."""

import logging
import time
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid
import json
import re

from app.services.s3_config_loader import get_chatbot_config
from app.services.bedrock_llm import get_bedrock_service
from app.services.athena import get_athena_service, AthenaQueryError
from app.services.s3_client import get_s3_client_service
from app.knowledge.schema_resolver import get_schema_resolver
from app.utils.sql_utils import validate_sql, sanitize_sql, add_limit_clause
from app.utils.result_utils import recommend_charts
from app.models.chat import (
    QueryRequest, QueryResponse, QueryOptions, ResultPreview, 
    AgentStep, QueryError, ChatSession, ChatMessage as ChatMessageModel
)
from app.models.visualization import ChartConfig

logger = logging.getLogger(__name__)


# In-memory session store (replace with Redis/DynamoDB in production)
_sessions: Dict[str, ChatSession] = {}
_pending_responses: Dict[str, QueryResponse] = {}
_streaming_queues: Dict[str, asyncio.Queue] = {}


class ConversationMemory:
    """Simple session-based conversation memory."""
    
    MAX_HISTORY = 5  # Keep last 5 Q&A pairs for context
    
    def __init__(self):
        self._memory: Dict[str, List[Dict[str, str]]] = {}
    
    def add_interaction(self, session_id: str, question: str, sql: str, summary: str):
        """Add a Q&A interaction to memory."""
        if session_id not in self._memory:
            self._memory[session_id] = []
        
        self._memory[session_id].append({
            "question": question,
            "sql": sql,
            "summary": summary
        })
        
        # Keep only last N interactions
        if len(self._memory[session_id]) > self.MAX_HISTORY:
            self._memory[session_id] = self._memory[session_id][-self.MAX_HISTORY:]
    
    def get_context(self, session_id: str) -> str:
        """Get formatted conversation history for context."""
        if session_id not in self._memory or not self._memory[session_id]:
            return ""
        
        history = []
        for i, interaction in enumerate(self._memory[session_id], 1):
            history.append(f"""
Previous Question {i}: {interaction['question']}
SQL Used: {interaction['sql']}
Result Summary: {interaction['summary']}
""")
        
        return "\n".join(history)
    
    def clear_session(self, session_id: str):
        """Clear memory for a session."""
        if session_id in self._memory:
            del self._memory[session_id]


# Global conversation memory
_conversation_memory = ConversationMemory()


class TextToSQLAgent:
    """Orchestrated agent for converting natural language questions to SQL with self-correction."""
    
    MAX_RETRIES = 3
    
    def __init__(self):
        self.schema_resolver = get_schema_resolver()
        self.athena_service = get_athena_service()
        self.s3_client = get_s3_client_service()
        self.bedrock_service = get_bedrock_service()
    
    @property
    def config(self):
        """Get current chatbot configuration."""
        return get_chatbot_config()
    
    def _emit_step(self, message_id: str, step_type: str, description: str, details: Dict = None):
        """Emit a step update for streaming."""
        if message_id in _streaming_queues:
            step = {
                "type": step_type,
                "description": description,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                _streaming_queues[message_id].put_nowait(step)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for message {message_id}")
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from LLM response."""
        # Try to find SQL in code blocks
        code_block_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", response)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Remove common prefixes
        sql = response.strip()
        for prefix in ["SQL Query:", "Here is the SQL:", "Query:", "Corrected SQL:", "SQL:"]:
            if sql.upper().startswith(prefix.upper()):
                sql = sql[len(prefix):].strip()
        
        return sql
    
    def _retrieve_schema(self, question: str, message_id: str) -> tuple:
        """Retrieve relevant database schema information."""
        self._emit_step(message_id, "retrieval", "🔍 Searching for relevant tables and columns...")
        
        context = self.schema_resolver.resolve_schema_context(question)
        formatted = self.schema_resolver.format_schema_for_prompt(context)
        
        tables = [t.name for t in context.relevant_tables]
        self._emit_step(message_id, "retrieval", f"📊 Found {len(tables)} relevant tables: {', '.join(tables)}")
        
        return formatted, context
    
    def _generate_sql(self, question: str, schema_context: str, message_id: str, session_id: str) -> str:
        """Generate SQL from question and schema, with conversation context."""
        self._emit_step(message_id, "thinking", "🧠 Analyzing question and generating SQL...")
        
        database = self.config.athena.database
        
        # Get conversation history for context
        conversation_history = _conversation_memory.get_context(session_id)
        
        # Build context-aware prompt
        history_section = ""
        if conversation_history:
            self._emit_step(message_id, "memory", "💾 Using conversation history for context...")
            history_section = f"""
PREVIOUS CONVERSATION CONTEXT:
{conversation_history}

Use this context to understand references like "those", "that data", "the same customers", etc.
"""

        prompt = f"""Given this database schema:

{schema_context}
{history_section}
Generate a SQL query for the current question: {question}

CRITICAL RULES:
- Database is '{database}' - access tables directly by name (e.g., SELECT * FROM products)
- NEVER use database prefixes like 'default.products' or '{database}.products'
- Use Presto SQL dialect (AWS Athena)
- Cast string columns to appropriate types when needed (e.g., CAST(price AS DOUBLE))
- Handle NULLs with COALESCE when appropriate
- Add meaningful column aliases
- If the question references previous data (like "those customers" or "that order"), use the previous SQL as a guide

Return ONLY the SQL query, no explanations or markdown."""

        sql = self.bedrock_service.generate_text(
            prompt,
            system_prompt=f"You are an expert SQL developer with conversation memory. Generate valid Presto SQL. Use table names directly without any database prefix. Pay attention to conversation context.",
            temperature=0.1
        )
        
        sql = self._extract_sql(sql)
        self._emit_step(message_id, "sql_generated", "✏️ Generated SQL query", {"sql": sql})
        
        return sql
    
    def _fix_sql(self, original_sql: str, error_message: str, schema_context: str, message_id: str) -> str:
        """Fix a failed SQL query."""
        self._emit_step(message_id, "thinking", "🔧 Analyzing error and fixing SQL...")
        
        database = self.config.athena.database
        
        prompt = f"""The following SQL query failed:

```sql
{original_sql}
```

Error: {error_message}

Schema context:
{schema_context}

Fix the SQL query to resolve this error. Common issues and solutions:
- "TABLE_NOT_FOUND: awsdatacatalog.default.X" -> Remove the database prefix, use just the table name
- Column not found -> Verify column names exactly match schema
- Type errors -> Cast string columns to appropriate types
- Syntax errors -> Check Presto SQL syntax

IMPORTANT: Use table names directly (e.g., 'products') not '{database}.products' or 'default.products'.

Return ONLY the corrected SQL query, no explanations."""

        fixed_sql = self.bedrock_service.generate_text(
            prompt,
            system_prompt=f"You are an expert at debugging SQL. Fix the query. Use table names directly without any database prefix.",
            temperature=0.1
        )
        
        fixed_sql = self._extract_sql(fixed_sql)
        self._emit_step(message_id, "sql_fixed", "🔧 Generated corrected SQL", {"sql": fixed_sql})
        
        return fixed_sql
    
    def _execute_sql(self, sql: str, message_id: str) -> tuple:
        """Execute SQL and return result or error."""
        self._emit_step(message_id, "executing", "⚡ Executing query in Athena...")
        
        # Validate SQL first
        is_valid, validation_error = validate_sql(sql)
        if not is_valid:
            self._emit_step(message_id, "error", f"❌ SQL validation failed: {validation_error}")
            return None, None, f"SQL validation error: {validation_error}"
        
        try:
            max_rows = self.config.features.default_max_rows
            sql_with_limit = add_limit_clause(sql, max_rows)
            
            result, query_id = self.athena_service.execute_query(
                sanitize_sql(sql_with_limit),
                max_rows=max_rows
            )
            
            self._emit_step(message_id, "success", f"✅ Query returned {result.total_rows} rows", {
                "row_count": result.total_rows,
                "columns": result.columns
            })
            
            return result, query_id, None
            
        except AthenaQueryError as e:
            self._emit_step(message_id, "error", f"❌ Query failed: {str(e)[:100]}...")
            return None, None, str(e)
        
        except Exception as e:
            self._emit_step(message_id, "error", f"❌ Unexpected error: {str(e)[:100]}")
            return None, None, str(e)
    
    async def _generate_summary(
        self,
        question: str,
        sql: str,
        result: ResultPreview
    ) -> str:
        """Generate natural language summary of results."""
        sample_data = []
        for i, row in enumerate(result.rows[:10]):
            row_dict = dict(zip(result.columns, row))
            sample_data.append(row_dict)
        
        prompt = f"""Summarize this data query result concisely:

Question: {question}

SQL: {sql}

Results ({result.total_rows} rows):
{json.dumps(sample_data, indent=2, default=str)}

Provide a 2-3 sentence business summary focusing on key insights."""
        
        response = self.bedrock_service.generate_text(
            prompt,
            system_prompt="You are a data analyst. Be concise and insightful.",
            temperature=0.3
        )
        
        return response.strip()
    
    async def process_query_background(
        self,
        request: QueryRequest,
        session_id: str,
        message_id: str
    ):
        """Process query in background (for streaming support)."""
        await self.process_query(request, session_id, message_id)
    
    async def process_query(
        self,
        request: QueryRequest,
        session_id: str = None,
        message_id: str = None
    ) -> QueryResponse:
        """
        Process a natural language query with self-correcting logic and session memory.
        """
        start_time = time.time()
        session_id = session_id or request.session_id or str(uuid.uuid4())
        message_id = message_id or str(uuid.uuid4())
        
        # Initialize session
        session = _sessions.get(session_id) or ChatSession(id=session_id)
        _sessions[session_id] = session
        
        # Create streaming queue if not exists
        if message_id not in _streaming_queues:
            _streaming_queues[message_id] = asyncio.Queue(maxsize=100)
        
        # Create/update response
        response = _pending_responses.get(message_id) or QueryResponse(
            session_id=session_id,
            message_id=message_id,
            status="running"
        )
        response.status = "running"
        _pending_responses[message_id] = response
        
        try:
            self._emit_step(message_id, "start", "🚀 Starting query processing...")
            
            # Step 1: Retrieve schema
            schema_context, context = self._retrieve_schema(request.question, message_id)
            
            # Step 2: Generate SQL (with conversation memory)
            current_sql = self._generate_sql(request.question, schema_context, message_id, session_id)
            
            # Step 3: Execute with retry loop
            result = None
            query_id = None
            last_error = None
            
            for attempt in range(self.MAX_RETRIES):
                result, query_id, error = self._execute_sql(current_sql, message_id)
                
                if result is not None:
                    # Success!
                    break
                
                last_error = error
                
                if attempt < self.MAX_RETRIES - 1:
                    self._emit_step(message_id, "thinking", f"🔄 Retry {attempt + 2}/{self.MAX_RETRIES}...")
                    current_sql = self._fix_sql(current_sql, error, schema_context, message_id)
            
            # Step 4: Process results
            if result is not None:
                response.result_preview = result
                response.sql = current_sql
                
                # Generate summary
                self._emit_step(message_id, "summarizing", "📝 Generating summary...")
                summary = await self._generate_summary(
                    request.question,
                    current_sql,
                    result
                )
                response.answer_summary = summary
                
                # Add to conversation memory
                _conversation_memory.add_interaction(
                    session_id,
                    request.question,
                    current_sql,
                    summary
                )
                self._emit_step(message_id, "memory", "💾 Saved to conversation memory")
                
                # Recommend charts
                if request.options and request.options.visualization_mode != "table_only":
                    self._emit_step(message_id, "charting", "📊 Analyzing data for visualization...")
                    chart_rec = recommend_charts(
                        result,
                        request.question,
                        allow_advanced=request.options.allow_advanced_charts if request.options else True
                    )
                    response.quick_chart = chart_rec.quick_chart
                    response.alternative_charts = chart_rec.alternative_charts
                
                response.status = "completed"
            else:
                # All retries failed
                response.status = "failed"
                response.error = QueryError(
                    message=f"Query failed after {self.MAX_RETRIES} attempts: {last_error}",
                    error_type="QueryExecutionError"
                )
                response.sql = current_sql
                response.answer_summary = f"I was unable to execute this query successfully. The error was: {last_error}"
            
            response.execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update session
            session.messages.append(ChatMessageModel(
                role="user",
                content=request.question
            ))
            session.messages.append(ChatMessageModel(
                role="assistant",
                content=response.answer_summary or "",
                response=response
            ))
            session.updated_at = datetime.utcnow()
            
            if not session.title and len(session.messages) >= 2:
                session.title = request.question[:50]
            
            self._emit_step(message_id, "done", "✅ Processing complete")
            
            return response
            
        except Exception as e:
            logger.exception(f"Query processing failed: {e}")
            self._emit_step(message_id, "error", f"❌ Error: {str(e)}")
            
            response.status = "failed"
            response.error = QueryError(
                message=str(e),
                error_type=type(e).__name__
            )
            response.execution_time_ms = int((time.time() - start_time) * 1000)
            
            self._emit_step(message_id, "done", "❌ Processing failed")
            
            return response
        
        finally:
            # Clean up streaming queue after a delay
            asyncio.get_event_loop().call_later(
                60, 
                lambda: _streaming_queues.pop(message_id, None)
            )
            _pending_responses[message_id] = response


async def stream_agent_steps(message_id: str) -> AsyncGenerator[Dict, None]:
    """Stream agent thinking steps for a message."""
    if message_id not in _streaming_queues:
        return
    
    queue = _streaming_queues[message_id]
    
    while True:
        try:
            step = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield step
            
            if step.get("type") == "done":
                break
                
        except asyncio.TimeoutError:
            yield {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.error(f"Stream error: {e}")
            break


def get_session(session_id: str) -> Optional[ChatSession]:
    """Get a session by ID."""
    return _sessions.get(session_id)


def get_all_sessions() -> List[ChatSession]:
    """Get all sessions."""
    return list(_sessions.values())


def get_pending_response(message_id: str) -> Optional[QueryResponse]:
    """Get a pending response by message ID."""
    return _pending_responses.get(message_id)


def delete_session(session_id: str) -> bool:
    """Delete a session and its memory."""
    if session_id in _sessions:
        del _sessions[session_id]
        _conversation_memory.clear_session(session_id)
        return True
    return False


# Singleton agent instance
_agent: Optional[TextToSQLAgent] = None


def get_text_to_sql_agent() -> TextToSQLAgent:
    """Get singleton agent instance."""
    global _agent
    if _agent is None:
        _agent = TextToSQLAgent()
    return _agent
