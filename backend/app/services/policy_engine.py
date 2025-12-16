"""Policy Engine - Transforms user feedback into actionable SQL generation hints."""

import logging
import re
from typing import Optional, List, Dict, Set
from datetime import datetime, timedelta

from app.models.feedback import (
    FeedbackRecord, FeedbackType, PolicyHint, FeedbackStats
)
from app.services.rlhf_store import RLHFStore, get_rlhf_store

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Evolves SQL generation policies based on accumulated user feedback.
    
    This engine analyzes patterns from thumbs up/down feedback and generates
    actionable hints that are injected into the LLM prompt for SQL generation.
    """
    
    # Pattern detection thresholds
    MIN_FEEDBACK_FOR_HINT = 2  # Minimum feedback count to generate a hint
    NEGATIVE_THRESHOLD = 0.4  # Generate "avoid" hint if success rate below this
    POSITIVE_THRESHOLD = 0.8  # Generate "prefer" hint if success rate above this
    
    # Common SQL patterns to track
    SQL_PATTERNS = [
        (r'GROUP\s+BY', 'GROUP BY'),
        (r'JOIN\s+', 'JOIN'),
        (r'LEFT\s+JOIN', 'LEFT JOIN'),
        (r'INNER\s+JOIN', 'INNER JOIN'),
        (r'CAST\s*\(', 'CAST'),
        (r'COALESCE\s*\(', 'COALESCE'),
        (r'CASE\s+WHEN', 'CASE WHEN'),
        (r'ORDER\s+BY', 'ORDER BY'),
        (r'HAVING\s+', 'HAVING'),
        (r'DISTINCT\s+', 'DISTINCT'),
        (r'COUNT\s*\(', 'COUNT'),
        (r'SUM\s*\(', 'SUM'),
        (r'AVG\s*\(', 'AVG'),
        (r'MAX\s*\(', 'MAX'),
        (r'MIN\s*\(', 'MIN'),
        (r'WHERE\s+.*\s+IN\s*\(', 'WHERE IN'),
        (r'WHERE\s+.*\s+LIKE\s+', 'WHERE LIKE'),
        (r'WHERE\s+.*\s+BETWEEN\s+', 'WHERE BETWEEN'),
        (r'LIMIT\s+\d+', 'LIMIT'),
        (r'DATE_TRUNC', 'DATE_TRUNC'),
        (r'TO_DATE', 'TO_DATE'),
        (r'SUBSTRING', 'SUBSTRING'),
    ]
    
    def __init__(self, store: Optional[RLHFStore] = None):
        """
        Initialize the policy engine.
        
        Args:
            store: RLHF store instance. Uses singleton if not provided.
        """
        self.store = store or get_rlhf_store()
    
    def extract_tables_from_sql(self, sql: str) -> List[str]:
        """
        Extract table names from a SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of table names found in the query
        """
        tables = set()
        
        # Match FROM and JOIN clauses
        patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                # Filter out common SQL keywords that might match
                if match.upper() not in ('SELECT', 'WHERE', 'AND', 'OR', 'ON', 'AS'):
                    tables.add(match.lower())
        
        return list(tables)
    
    def extract_sql_patterns(self, sql: str) -> List[str]:
        """
        Identify SQL patterns used in a query.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of pattern names found
        """
        patterns_found = []
        
        for pattern_regex, pattern_name in self.SQL_PATTERNS:
            if re.search(pattern_regex, sql, re.IGNORECASE):
                patterns_found.append(pattern_name)
        
        return patterns_found
    
    def record_feedback(
        self,
        message_id: str,
        session_id: str,
        question: str,
        sql: str,
        feedback_type: FeedbackType,
        reason: Optional[str] = None
    ) -> FeedbackRecord:
        """
        Record user feedback and update policies accordingly.
        
        Args:
            message_id: ID of the message being rated
            session_id: Session ID
            question: Original user question
            sql: Generated SQL query
            feedback_type: Thumbs up or down
            reason: Optional reason for feedback
            
        Returns:
            The created feedback record
        """
        # Extract metadata
        tables = self.extract_tables_from_sql(sql)
        patterns = self.extract_sql_patterns(sql)
        
        # Create feedback record
        record = FeedbackRecord(
            message_id=message_id,
            session_id=session_id,
            question=question,
            sql=sql,
            feedback_type=feedback_type,
            reason=reason,
            metadata={
                "tables": tables,
                "patterns": patterns,
                "question_length": len(question),
                "sql_length": len(sql),
            }
        )
        
        # Save to store
        self.store.save_feedback(record)
        
        # Trigger policy update
        self._update_policies_from_feedback(record)
        
        logger.info(
            f"Recorded {feedback_type.value} feedback for message {message_id} "
            f"(tables: {tables}, patterns: {patterns})"
        )
        
        return record
    
    def _update_policies_from_feedback(self, record: FeedbackRecord) -> None:
        """
        Update policies immediately after receiving feedback.
        
        Args:
            record: The new feedback record
        """
        tables = record.metadata.get("tables", [])
        patterns = record.metadata.get("patterns", [])
        
        # For negative feedback, analyze what might have gone wrong
        if record.feedback_type == FeedbackType.THUMBS_DOWN:
            # Check if this is a recurring issue with specific tables
            for table in tables:
                table_feedback = self.store.get_feedback_for_tables([table])
                negative_count = sum(
                    1 for f in table_feedback 
                    if f.feedback_type == FeedbackType.THUMBS_DOWN
                )
                total_count = len(table_feedback)
                
                if total_count >= self.MIN_FEEDBACK_FOR_HINT:
                    success_rate = 1 - (negative_count / total_count)
                    
                    if success_rate < self.NEGATIVE_THRESHOLD:
                        # Create an "avoid" or "caution" hint for this table
                        hint = PolicyHint(
                            hint_type="caution",
                            description=f"Table '{table}' has a low success rate ({success_rate:.0%}). Pay extra attention to column types and joins.",
                            weight=min(0.9, 0.5 + (0.1 * negative_count)),
                            tables=[table],
                        )
                        self.store.add_policy_hint(hint)
            
            # Check for pattern-specific issues
            for pattern in patterns:
                pattern_feedback = self._get_feedback_by_sql_pattern(pattern)
                negative_pattern_count = sum(
                    1 for f in pattern_feedback 
                    if f.feedback_type == FeedbackType.THUMBS_DOWN
                )
                
                if negative_pattern_count >= self.MIN_FEEDBACK_FOR_HINT:
                    hint = PolicyHint(
                        hint_type="tip",
                        description=f"SQL pattern '{pattern}' has caused issues. Ensure proper syntax and type compatibility.",
                        weight=0.5,
                        tables=tables,
                        pattern=pattern,
                    )
                    self.store.add_policy_hint(hint)
            
            # If there's a specific reason, create a direct hint
            if record.reason:
                hint = PolicyHint(
                    hint_type="user_feedback",
                    description=f"User reported: {record.reason}",
                    weight=0.7,
                    tables=tables,
                )
                self.store.add_policy_hint(hint)
        
        # For positive feedback, reinforce successful patterns
        elif record.feedback_type == FeedbackType.THUMBS_UP:
            # Create "prefer" hints for successful patterns (less aggressive)
            if patterns and len(tables) > 0:
                # Only create prefer hints for patterns that have good track records
                for pattern in patterns:
                    pattern_feedback = self._get_feedback_by_sql_pattern(pattern)
                    positive_count = sum(
                        1 for f in pattern_feedback 
                        if f.feedback_type == FeedbackType.THUMBS_UP
                    )
                    total = len(pattern_feedback)
                    
                    if total >= self.MIN_FEEDBACK_FOR_HINT:
                        success_rate = positive_count / total
                        
                        if success_rate >= self.POSITIVE_THRESHOLD:
                            hint = PolicyHint(
                                hint_type="prefer",
                                description=f"Pattern '{pattern}' works well with tables: {', '.join(tables)}",
                                weight=0.5,
                                tables=tables,
                                pattern=pattern,
                            )
                            self.store.add_policy_hint(hint)
    
    def _get_feedback_by_sql_pattern(self, pattern_name: str) -> List[FeedbackRecord]:
        """Get feedback records that used a specific SQL pattern."""
        all_feedback = self.store.get_all_feedback()
        return [
            f for f in all_feedback
            if pattern_name in f.metadata.get("patterns", [])
        ]
    
    def get_policy_hints(
        self,
        question: str,
        tables: List[str]
    ) -> List[PolicyHint]:
        """
        Get relevant policy hints for a query context.
        
        Args:
            question: User's question
            tables: Tables that will be involved in the query
            
        Returns:
            List of relevant policy hints
        """
        hints = self.store.get_hints_for_context(tables)
        
        # Also check for question-pattern matches in recent negative feedback
        recent_negative = [
            r for r in self.store.get_recent_feedback(20)
            if r.feedback_type == FeedbackType.THUMBS_DOWN
        ]
        
        # Check for similar questions that failed
        for record in recent_negative:
            similarity = self._question_similarity(question, record.question)
            if similarity > 0.7:
                hint = PolicyHint(
                    hint_type="warning",
                    description=f"A similar question previously failed. Consider alternative approaches.",
                    weight=0.6,
                    tables=record.metadata.get("tables", []),
                )
                hints.append(hint)
                break  # Only add one such warning
        
        return hints
    
    def _question_similarity(self, q1: str, q2: str) -> float:
        """
        Calculate simple similarity between two questions.
        
        Uses word overlap as a basic similarity metric.
        """
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)  # Jaccard similarity
    
    def format_hints_for_prompt(self, hints: List[PolicyHint]) -> str:
        """
        Format policy hints as a section for the LLM prompt.
        
        Args:
            hints: List of policy hints to format
            
        Returns:
            Formatted string for prompt injection
        """
        if not hints:
            return ""
        
        lines = ["\nBASED ON PREVIOUS USER FEEDBACK:"]
        
        # Group by hint type
        hint_groups: Dict[str, List[PolicyHint]] = {}
        for hint in hints:
            key = hint.hint_type.upper()
            if key not in hint_groups:
                hint_groups[key] = []
            hint_groups[key].append(hint)
        
        # Format each group
        type_icons = {
            "PREFER": "✓",
            "AVOID": "✗",
            "CAUTION": "⚠",
            "TIP": "💡",
            "WARNING": "⚠",
            "USER_FEEDBACK": "📝",
        }
        
        for hint_type, group_hints in hint_groups.items():
            icon = type_icons.get(hint_type, "•")
            for hint in group_hints[:3]:  # Limit per type
                lines.append(f"- {icon} {hint_type}: {hint.description}")
        
        lines.append("")  # Empty line after hints
        
        return "\n".join(lines)
    
    def get_feedback_stats(self) -> FeedbackStats:
        """Get aggregated feedback statistics."""
        return self.store.get_aggregated_stats()
    
    def analyze_and_update_policies(self) -> int:
        """
        Run full policy analysis on all feedback data.
        
        This can be called periodically to recalculate all policies.
        
        Returns:
            Number of hints generated/updated
        """
        all_feedback = self.store.get_all_feedback()
        
        if len(all_feedback) < self.MIN_FEEDBACK_FOR_HINT:
            return 0
        
        hints_created = 0
        
        # Analyze by table
        table_stats: Dict[str, Dict[str, int]] = {}
        for record in all_feedback:
            for table in record.metadata.get("tables", []):
                if table not in table_stats:
                    table_stats[table] = {"up": 0, "down": 0}
                if record.feedback_type == FeedbackType.THUMBS_UP:
                    table_stats[table]["up"] += 1
                else:
                    table_stats[table]["down"] += 1
        
        for table, stats in table_stats.items():
            total = stats["up"] + stats["down"]
            if total >= self.MIN_FEEDBACK_FOR_HINT:
                success_rate = stats["up"] / total
                
                if success_rate < self.NEGATIVE_THRESHOLD:
                    hint = PolicyHint(
                        hint_type="caution",
                        description=f"Table '{table}' has {success_rate:.0%} success rate. Verify column types and relationships.",
                        weight=0.7,
                        tables=[table],
                        source_feedback_count=total,
                    )
                    self.store.add_policy_hint(hint)
                    hints_created += 1
        
        logger.info(f"Policy analysis complete. Created/updated {hints_created} hints.")
        return hints_created


# Singleton instance
_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """Get singleton policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
