"""SQL Utilities - Validation, sanitization, and formatting."""

import re
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """Exception for SQL validation failures."""
    pass


DANGEROUS_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bREPLACE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
]

REQUIRED_KEYWORDS = [r"\bSELECT\b"]


def validate_sql(sql: str, allow_dangerous: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate SQL for safety and correctness.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"
    
    sql_upper = sql.upper()
    
    # Check for required SELECT
    has_select = any(re.search(kw, sql_upper) for kw in REQUIRED_KEYWORDS)
    if not has_select:
        return False, "Query must contain SELECT statement"
    
    # Check for dangerous keywords
    if not allow_dangerous:
        for pattern in DANGEROUS_KEYWORDS:
            if re.search(pattern, sql_upper):
                keyword = pattern.replace(r"\b", "").replace("\\", "")
                return False, f"Dangerous keyword detected: {keyword}"
    
    # Check for balanced parentheses
    if sql.count("(") != sql.count(")"):
        return False, "Unbalanced parentheses in query"
    
    # Check for balanced quotes
    single_quotes = len(re.findall(r"(?<!')'(?!')", sql))
    if single_quotes % 2 != 0:
        return False, "Unbalanced single quotes in query"
    
    return True, None


def sanitize_sql(sql: str) -> str:
    """
    Clean up and format SQL query.
    """
    # Remove leading/trailing whitespace
    sql = sql.strip()
    
    # Remove multiple consecutive spaces
    sql = re.sub(r" +", " ", sql)
    
    # Remove trailing semicolons (Athena doesn't need them)
    sql = sql.rstrip(";")
    
    # Ensure consistent line endings
    sql = sql.replace("\r\n", "\n")
    
    return sql


def format_sql(sql: str) -> str:
    """
    Basic SQL formatting for readability.
    """
    keywords = [
        "SELECT", "FROM", "WHERE", "AND", "OR", "ORDER BY",
        "GROUP BY", "HAVING", "LIMIT", "OFFSET", "JOIN",
        "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN",
        "ON", "AS", "UNION", "INTERSECT", "EXCEPT", "WITH"
    ]
    
    formatted = sql
    
    # Add newlines before major keywords
    for kw in ["FROM", "WHERE", "AND", "OR", "ORDER BY", "GROUP BY", 
               "HAVING", "LIMIT", "JOIN", "LEFT JOIN", "RIGHT JOIN",
               "INNER JOIN", "OUTER JOIN"]:
        pattern = rf"(\s+)({kw}\s)"
        formatted = re.sub(pattern, rf"\n{kw} ", formatted, flags=re.IGNORECASE)
    
    return formatted


def extract_table_references(sql: str) -> List[str]:
    """
    Extract table names referenced in SQL query.
    
    Returns:
        List of table names
    """
    tables = set()
    
    # Match FROM table pattern
    from_pattern = r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_\.]*)"
    for match in re.finditer(from_pattern, sql, re.IGNORECASE):
        tables.add(match.group(1))
    
    # Match JOIN table pattern
    join_pattern = r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_\.]*)"
    for match in re.finditer(join_pattern, sql, re.IGNORECASE):
        tables.add(match.group(1))
    
    return list(tables)


def add_limit_clause(sql: str, limit: int) -> str:
    """
    Add or update LIMIT clause in SQL query.
    """
    # Check if limit already exists
    if re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE):
        # Replace existing limit
        return re.sub(
            r"\bLIMIT\s+\d+",
            f"LIMIT {limit}",
            sql,
            flags=re.IGNORECASE
        )
    else:
        # Add limit
        return f"{sql.rstrip(';')} LIMIT {limit}"


def wrap_with_cte(sql: str, cte_name: str = "source_data") -> str:
    """
    Wrap a query in a CTE for further processing.
    """
    return f"""WITH {cte_name} AS (
{sql}
)
SELECT * FROM {cte_name}"""


def estimate_query_complexity(sql: str) -> str:
    """
    Estimate query complexity based on syntax.
    
    Returns:
        'simple', 'moderate', or 'complex'
    """
    sql_upper = sql.upper()
    
    complexity_indicators = {
        "complex": [
            r"\bWITH\b.*\bAS\b",
            r"\bWINDOW\b",
            r"\bPARTITION BY\b",
            r"SELECT.*SELECT",  # Subqueries
            r"\bUNION\b",
            r"\bINTERSECT\b",
        ],
        "moderate": [
            r"\bJOIN\b",
            r"\bGROUP BY\b",
            r"\bHAVING\b",
            r"\bCASE\b.*\bWHEN\b",
            r"\bDISTINCT\b"
        ]
    }
    
    for pattern in complexity_indicators["complex"]:
        if re.search(pattern, sql_upper):
            return "complex"
    
    for pattern in complexity_indicators["moderate"]:
        if re.search(pattern, sql_upper):
            return "moderate"
    
    return "simple"
