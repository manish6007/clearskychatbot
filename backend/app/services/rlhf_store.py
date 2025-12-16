"""RLHF Store - JSON-based persistent storage for feedback and policies."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from threading import Lock
from filelock import FileLock

from app.models.feedback import (
    FeedbackRecord, FeedbackType, PolicyHint, PolicyState, FeedbackStats
)

logger = logging.getLogger(__name__)


class RLHFStore:
    """
    JSON-based persistent storage for RLHF feedback records and learned policies.
    
    Uses file locking for thread-safety and atomic writes for data integrity.
    """
    
    DEFAULT_STORAGE_DIR = "rlhf_data"
    FEEDBACK_FILE = "feedback_records.json"
    POLICY_FILE = "policy_state.json"
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the RLHF store.
        
        Args:
            storage_dir: Directory for storing JSON files. Defaults to ./rlhf_data
        """
        self.storage_dir = Path(storage_dir or self.DEFAULT_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.storage_dir / self.FEEDBACK_FILE
        self.policy_file = self.storage_dir / self.POLICY_FILE
        
        # File locks for thread safety
        self.feedback_lock = FileLock(str(self.feedback_file) + ".lock")
        self.policy_lock = FileLock(str(self.policy_file) + ".lock")
        
        # In-memory cache
        self._feedback_cache: List[FeedbackRecord] = []
        self._policy_cache: Optional[PolicyState] = None
        self._cache_loaded = False
        self._memory_lock = Lock()
        
        # Initialize files if they don't exist
        self._initialize_storage()
        
        logger.info(f"RLHFStore initialized with storage at {self.storage_dir}")
    
    def _initialize_storage(self) -> None:
        """Create storage files if they don't exist."""
        if not self.feedback_file.exists():
            self._write_json(self.feedback_file, {"records": []}, self.feedback_lock)
        
        if not self.policy_file.exists():
            initial_policy = PolicyState()
            self._write_json(
                self.policy_file, 
                initial_policy.model_dump(mode='json'), 
                self.policy_lock
            )
    
    def _read_json(self, file_path: Path, lock: FileLock) -> Dict[str, Any]:
        """Read JSON file with locking."""
        with lock:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Error reading {file_path}: {e}")
                return {}
    
    def _write_json(self, file_path: Path, data: Dict[str, Any], lock: FileLock) -> None:
        """Write JSON file atomically with locking."""
        with lock:
            # Write to temp file first, then rename (atomic on most systems)
            temp_file = file_path.with_suffix('.tmp')
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                temp_file.replace(file_path)
            except Exception as e:
                logger.error(f"Error writing {file_path}: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                raise
    
    def _load_cache(self) -> None:
        """Load data into memory cache."""
        if self._cache_loaded:
            return
        
        with self._memory_lock:
            if self._cache_loaded:  # Double-check after lock
                return
            
            # Load feedback records
            feedback_data = self._read_json(self.feedback_file, self.feedback_lock)
            self._feedback_cache = [
                FeedbackRecord(**r) for r in feedback_data.get("records", [])
            ]
            
            # Load policy state
            policy_data = self._read_json(self.policy_file, self.policy_lock)
            if policy_data:
                self._policy_cache = PolicyState(**policy_data)
            else:
                self._policy_cache = PolicyState()
            
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._feedback_cache)} feedback records from cache")
    
    def save_feedback(self, record: FeedbackRecord) -> None:
        """
        Save a new feedback record.
        
        Args:
            record: The feedback record to save
        """
        self._load_cache()
        
        with self._memory_lock:
            self._feedback_cache.append(record)
        
        # Persist to disk
        feedback_data = {
            "records": [r.model_dump(mode='json') for r in self._feedback_cache]
        }
        self._write_json(self.feedback_file, feedback_data, self.feedback_lock)
        
        logger.info(f"Saved feedback {record.id} ({record.feedback_type.value})")
    
    def get_all_feedback(self) -> List[FeedbackRecord]:
        """Get all feedback records."""
        self._load_cache()
        return self._feedback_cache.copy()
    
    def get_feedback_by_message_id(self, message_id: str) -> Optional[FeedbackRecord]:
        """Get feedback for a specific message."""
        self._load_cache()
        for record in self._feedback_cache:
            if record.message_id == message_id:
                return record
        return None
    
    def get_feedback_for_tables(self, tables: List[str]) -> List[FeedbackRecord]:
        """
        Get feedback records that involve specific tables.
        
        Args:
            tables: List of table names to filter by
        """
        self._load_cache()
        
        matching = []
        tables_set = set(t.lower() for t in tables)
        
        for record in self._feedback_cache:
            record_tables = set(
                t.lower() for t in record.metadata.get("tables", [])
            )
            if record_tables & tables_set:  # Intersection
                matching.append(record)
        
        return matching
    
    def get_feedback_by_pattern(self, pattern: str) -> List[FeedbackRecord]:
        """
        Get feedback records matching a SQL pattern.
        
        Args:
            pattern: Regex pattern to match against SQL
        """
        self._load_cache()
        
        matching = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for record in self._feedback_cache:
                if regex.search(record.sql):
                    matching.append(record)
        except re.error as e:
            logger.warning(f"Invalid pattern regex: {e}")
        
        return matching
    
    def get_recent_feedback(self, limit: int = 50) -> List[FeedbackRecord]:
        """Get most recent feedback records."""
        self._load_cache()
        sorted_records = sorted(
            self._feedback_cache, 
            key=lambda r: r.timestamp, 
            reverse=True
        )
        return sorted_records[:limit]
    
    def get_aggregated_stats(self) -> FeedbackStats:
        """Calculate aggregated statistics from all feedback."""
        self._load_cache()
        
        stats = FeedbackStats()
        stats.total_feedback = len(self._feedback_cache)
        
        if not self._feedback_cache:
            return stats
        
        # Count by type
        stats.thumbs_up_count = sum(
            1 for r in self._feedback_cache 
            if r.feedback_type == FeedbackType.THUMBS_UP
        )
        stats.thumbs_down_count = stats.total_feedback - stats.thumbs_up_count
        
        # Success rate
        if stats.total_feedback > 0:
            stats.success_rate = stats.thumbs_up_count / stats.total_feedback
        
        # By table
        table_stats: Dict[str, Dict[str, int]] = {}
        for record in self._feedback_cache:
            for table in record.metadata.get("tables", []):
                if table not in table_stats:
                    table_stats[table] = {"thumbs_up": 0, "thumbs_down": 0}
                if record.feedback_type == FeedbackType.THUMBS_UP:
                    table_stats[table]["thumbs_up"] += 1
                else:
                    table_stats[table]["thumbs_down"] += 1
        stats.feedback_by_table = table_stats
        
        # Recent patterns (last 10 negative feedback)
        negative_feedback = [
            r for r in self._feedback_cache 
            if r.feedback_type == FeedbackType.THUMBS_DOWN
        ]
        negative_feedback.sort(key=lambda r: r.timestamp, reverse=True)
        stats.recent_patterns = [
            {
                "question": r.question[:100],
                "sql_snippet": r.sql[:200] if r.sql else "",
                "tables": r.metadata.get("tables", []),
                "reason": r.reason
            }
            for r in negative_feedback[:10]
        ]
        
        # Active hints count
        if self._policy_cache:
            stats.active_hints = len(self._policy_cache.hints)
        
        return stats
    
    # Policy management
    
    def get_policy_state(self) -> PolicyState:
        """Get the current policy state."""
        self._load_cache()
        return self._policy_cache or PolicyState()
    
    def save_policy_state(self, state: PolicyState) -> None:
        """Save the policy state."""
        self._load_cache()
        
        state.last_updated = datetime.utcnow()
        state.version += 1
        
        with self._memory_lock:
            self._policy_cache = state
        
        self._write_json(
            self.policy_file, 
            state.model_dump(mode='json'), 
            self.policy_lock
        )
        
        logger.info(f"Saved policy state v{state.version} with {len(state.hints)} hints")
    
    def add_policy_hint(self, hint: PolicyHint) -> None:
        """Add or update a policy hint."""
        state = self.get_policy_state()
        
        # Check if similar hint exists (same type and tables)
        existing_idx = None
        for i, existing in enumerate(state.hints):
            if (existing.hint_type == hint.hint_type and 
                set(existing.tables) == set(hint.tables) and
                existing.pattern == hint.pattern):
                existing_idx = i
                break
        
        if existing_idx is not None:
            # Update existing hint
            existing_hint = state.hints[existing_idx]
            existing_hint.source_feedback_count += 1
            existing_hint.weight = min(1.0, existing_hint.weight + 0.1)
            existing_hint.updated_at = datetime.utcnow()
            state.hints[existing_idx] = existing_hint
        else:
            # Add new hint
            state.hints.append(hint)
        
        self.save_policy_state(state)
    
    def get_hints_for_context(
        self, 
        tables: List[str], 
        min_weight: float = 0.3
    ) -> List[PolicyHint]:
        """
        Get policy hints relevant to a query context.
        
        Args:
            tables: Tables involved in the query
            min_weight: Minimum weight threshold
        """
        state = self.get_policy_state()
        
        tables_set = set(t.lower() for t in tables)
        relevant_hints = []
        
        for hint in state.hints:
            if hint.weight < min_weight:
                continue
            
            hint_tables = set(t.lower() for t in hint.tables)
            
            # Include if: tables overlap OR hint has no specific tables (general hint)
            if not hint_tables or hint_tables & tables_set:
                relevant_hints.append(hint)
        
        # Sort by weight descending
        relevant_hints.sort(key=lambda h: h.weight, reverse=True)
        
        return relevant_hints[:10]  # Limit to top 10 hints
    
    def clear_all_data(self) -> None:
        """Clear all stored data (for testing)."""
        with self._memory_lock:
            self._feedback_cache = []
            self._policy_cache = PolicyState()
            self._cache_loaded = True
        
        self._write_json(self.feedback_file, {"records": []}, self.feedback_lock)
        self._write_json(
            self.policy_file, 
            PolicyState().model_dump(mode='json'), 
            self.policy_lock
        )
        
        logger.info("Cleared all RLHF data")


# Singleton instance
_rlhf_store: Optional[RLHFStore] = None


def get_rlhf_store() -> RLHFStore:
    """Get singleton RLHF store instance."""
    global _rlhf_store
    if _rlhf_store is None:
        _rlhf_store = RLHFStore()
    return _rlhf_store
