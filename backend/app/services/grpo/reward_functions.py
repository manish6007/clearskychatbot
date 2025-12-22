"""Reward Functions for GRPO Text-to-SQL Training.

This module implements reward functions that score SQL completions based on:
1. SQL Validity - Syntactic correctness
2. Execution Success - Whether the query runs successfully
3. Result Quality - Relevance and completeness of results
4. Format Quality - SQL best practices and formatting
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from app.services.grpo.grpo_config import GRPOConfig

logger = logging.getLogger(__name__)


class RewardFunctions:
    """
    GRPO Reward Functions for Text-to-SQL.
    
    Each function returns a score between -1.0 and 1.0.
    Positive scores indicate good outcomes, negative scores indicate problems.
    
    Reward calculation follows GRPO methodology where:
    - Multiple reward signals are combined with configurable weights
    - Final reward is used to compute group-relative advantages
    """
    
    # SQL keywords for pattern detection
    SQL_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
        'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION',
        'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'
    }
    
    # Best practice patterns (positive)
    GOOD_PATTERNS = [
        (r'CAST\s*\(', 'type_casting'),
        (r'COALESCE\s*\(', 'null_handling'),
        (r'AS\s+\w+', 'column_aliasing'),
        (r'LIMIT\s+\d+', 'row_limiting'),
        (r'ORDER\s+BY', 'result_ordering'),
    ]
    
    # Anti-patterns (negative)
    BAD_PATTERNS = [
        (r'SELECT\s+\*', 'select_star'),  # SELECT * is often bad practice
        (r'\w+\.\w+\.\w+', 'triple_prefix'),  # database.schema.table prefix
        (r'--.*$', 'sql_comment'),  # Comments (might indicate confusion)
    ]
    
    def __init__(self, config: Optional[GRPOConfig] = None):
        self.config = config or GRPOConfig()
        self.weights = self.config.reward_weights
    
    def sql_validity_reward(self, sql: str) -> Tuple[float, Dict[str, Any]]:
        """
        Check SQL syntax validity.
        
        GRPO Step 2a: Score each completion for syntactic correctness.
        
        Returns:
            Tuple of (reward, details)
            - reward: -1.0 to 1.0
            - details: breakdown of checks
        """
        details = {
            "has_select": False,
            "has_from": False,
            "balanced_parens": False,
            "no_syntax_errors": True,
            "valid_structure": False
        }
        
        if not sql or not sql.strip():
            return -1.0, {"error": "Empty SQL query"}
        
        sql_upper = sql.upper()
        
        # Check for essential components
        details["has_select"] = "SELECT" in sql_upper
        details["has_from"] = "FROM" in sql_upper
        
        # Check balanced parentheses
        open_parens = sql.count('(')
        close_parens = sql.count(')')
        details["balanced_parens"] = open_parens == close_parens
        
        # Check for common syntax issues
        # Unclosed quotes
        single_quotes = sql.count("'")
        double_quotes = sql.count('"')
        details["no_syntax_errors"] = (single_quotes % 2 == 0) and (double_quotes % 2 == 0)
        
        # Validate structure (SELECT ... FROM ...)
        select_from_pattern = r'SELECT\s+.+\s+FROM\s+\w+'
        details["valid_structure"] = bool(re.search(select_from_pattern, sql_upper, re.DOTALL))
        
        # Calculate score
        score = 0.0
        if details["has_select"]:
            score += 0.3
        if details["has_from"]:
            score += 0.3
        if details["balanced_parens"]:
            score += 0.15
        if details["no_syntax_errors"]:
            score += 0.15
        if details["valid_structure"]:
            score += 0.1
        
        # Normalize to -1.0 to 1.0 range
        final_score = (score * 2) - 1.0  # 0->-1, 0.5->0, 1->1
        
        return round(final_score, 3), details
    
    def execution_reward(
        self, 
        sql: str, 
        execution_result: Optional[Dict[str, Any]] = None,
        execution_error: Optional[str] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Score based on execution success.
        
        GRPO Step 2b: Reward successful execution.
        
        Args:
            sql: The SQL query
            execution_result: Result from Athena (if available)
            execution_error: Error message (if failed)
            
        Returns:
            Tuple of (reward, details)
        """
        details = {
            "executed": False,
            "has_results": False,
            "row_count": 0,
            "error_type": None
        }
        
        if execution_error:
            # Classify error severity
            error_lower = execution_error.lower()
            
            if "syntax" in error_lower or "parse" in error_lower:
                details["error_type"] = "syntax_error"
                return -0.8, details
            elif "not found" in error_lower or "does not exist" in error_lower:
                details["error_type"] = "object_not_found"
                return -0.6, details
            elif "permission" in error_lower or "access" in error_lower:
                details["error_type"] = "permission_error"
                return -0.3, details
            elif "timeout" in error_lower:
                details["error_type"] = "timeout"
                return -0.2, details
            else:
                details["error_type"] = "unknown"
                return -0.5, details
        
        if execution_result:
            details["executed"] = True
            row_count = execution_result.get("total_rows", 0)
            details["row_count"] = row_count
            details["has_results"] = row_count > 0
            
            if row_count > 0:
                # Successful execution with results
                return 1.0, details
            else:
                # Executed but empty results (might be valid or might be wrong)
                return 0.3, details
        
        # No execution info available (simulation mode)
        # Use heuristic based on SQL complexity
        return 0.0, {"note": "execution_simulated"}
    
    def result_quality_reward(
        self,
        sql: str,
        question: str,
        execution_result: Optional[Dict[str, Any]] = None,
        expected_tables: Optional[List[str]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Assess result quality and relevance.
        
        GRPO Step 2c: Evaluate if the result answers the question.
        
        Args:
            sql: The SQL query
            question: Original user question
            execution_result: Query results (if available)
            expected_tables: Tables that should be used
            
        Returns:
            Tuple of (reward, details)
        """
        details = {
            "keyword_match": 0.0,
            "table_coverage": 0.0,
            "aggregation_match": False,
            "column_relevance": 0.0
        }
        
        question_lower = question.lower()
        sql_lower = sql.lower()
        
        # Check keyword relevance
        keywords = self._extract_keywords(question_lower)
        matches = sum(1 for kw in keywords if kw in sql_lower)
        details["keyword_match"] = matches / max(len(keywords), 1)
        
        # Check table usage
        if expected_tables:
            tables_in_sql = [t for t in expected_tables if t.lower() in sql_lower]
            details["table_coverage"] = len(tables_in_sql) / len(expected_tables)
        else:
            details["table_coverage"] = 0.5  # Neutral if no expected tables
        
        # Check for aggregate function usage based on question
        aggregate_keywords = ['total', 'sum', 'count', 'average', 'avg', 'max', 'min', 'how many']
        needs_aggregation = any(kw in question_lower for kw in aggregate_keywords)
        has_aggregation = any(
            agg in sql_lower for agg in ['sum(', 'count(', 'avg(', 'max(', 'min(']
        )
        details["aggregation_match"] = (needs_aggregation == has_aggregation) or has_aggregation
        
        # Calculate score
        score = (
            details["keyword_match"] * 0.3 +
            details["table_coverage"] * 0.4 +
            (0.3 if details["aggregation_match"] else 0.0)
        )
        
        # Normalize to -1.0 to 1.0
        final_score = (score * 2) - 1.0
        
        return round(final_score, 3), details
    
    def format_quality_reward(self, sql: str) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate SQL formatting and best practices.
        
        GRPO Step 2d: Reward well-formatted SQL.
        
        Returns:
            Tuple of (reward, details)
        """
        details = {
            "good_patterns": [],
            "bad_patterns": [],
            "readability_score": 0.0
        }
        
        # Check for good patterns
        for pattern, name in self.GOOD_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                details["good_patterns"].append(name)
        
        # Check for bad patterns
        for pattern, name in self.BAD_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                details["bad_patterns"].append(name)
        
        # Readability heuristics
        has_newlines = '\n' in sql
        has_proper_casing = any(kw in sql for kw in ['SELECT', 'FROM', 'WHERE', 'JOIN'])
        has_aliases = bool(re.search(r'\bAS\s+\w+', sql, re.IGNORECASE))
        
        readability = 0.0
        if has_proper_casing:
            readability += 0.33
        if has_aliases:
            readability += 0.33
        if has_newlines:
            readability += 0.34
        details["readability_score"] = readability
        
        # Calculate score
        good_score = min(len(details["good_patterns"]) * 0.2, 0.5)
        bad_score = min(len(details["bad_patterns"]) * 0.2, 0.5)
        readability_bonus = details["readability_score"] * 0.3
        
        score = 0.5 + good_score + readability_bonus - bad_score
        
        # Normalize to -1.0 to 1.0
        final_score = (score * 2) - 1.0
        final_score = max(-1.0, min(1.0, final_score))
        
        return round(final_score, 3), details
    
    def compute_total_reward(
        self,
        sql: str,
        question: str,
        execution_result: Optional[Dict[str, Any]] = None,
        execution_error: Optional[str] = None,
        expected_tables: Optional[List[str]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute weighted total reward from all components.
        
        GRPO Step 2 Complete: Combine all reward signals.
        
        Returns:
            Tuple of (total_reward, breakdown_dict)
        """
        breakdown = {}
        
        # 1. SQL Validity
        validity_score, validity_details = self.sql_validity_reward(sql)
        breakdown["sql_validity"] = {
            "score": validity_score,
            "weight": self.weights["sql_validity"],
            "weighted": validity_score * self.weights["sql_validity"],
            "details": validity_details
        }
        
        # 2. Execution Success
        exec_score, exec_details = self.execution_reward(sql, execution_result, execution_error)
        breakdown["execution_success"] = {
            "score": exec_score,
            "weight": self.weights["execution_success"],
            "weighted": exec_score * self.weights["execution_success"],
            "details": exec_details
        }
        
        # 3. Result Quality
        quality_score, quality_details = self.result_quality_reward(
            sql, question, execution_result, expected_tables
        )
        breakdown["result_quality"] = {
            "score": quality_score,
            "weight": self.weights["result_quality"],
            "weighted": quality_score * self.weights["result_quality"],
            "details": quality_details
        }
        
        # 4. Format Quality
        format_score, format_details = self.format_quality_reward(sql)
        breakdown["format_quality"] = {
            "score": format_score,
            "weight": self.weights["format_quality"],
            "weighted": format_score * self.weights["format_quality"],
            "details": format_details
        }
        
        # Calculate total
        total = sum(b["weighted"] for b in breakdown.values())
        
        return round(total, 4), breakdown
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Remove common words
        stop_words = {
            'show', 'me', 'get', 'find', 'list', 'all', 'the', 'a', 'an', 
            'of', 'in', 'for', 'with', 'by', 'from', 'to', 'and', 'or'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords


# Singleton instance
_reward_functions: Optional[RewardFunctions] = None


def get_reward_functions(config: Optional[GRPOConfig] = None) -> RewardFunctions:
    """Get singleton reward functions instance."""
    global _reward_functions
    if _reward_functions is None or config is not None:
        _reward_functions = RewardFunctions(config)
    return _reward_functions
