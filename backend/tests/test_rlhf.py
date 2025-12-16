"""Test suite for RLHF feedback and policy engine."""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.feedback import (
    FeedbackType, FeedbackRecord, FeedbackRequest, 
    PolicyHint, PolicyState, FeedbackStats
)
from app.services.rlhf_store import RLHFStore
from app.services.policy_engine import PolicyEngine


def test_feedback_models():
    """Test feedback Pydantic models."""
    print("Testing feedback models...")
    
    # Test FeedbackRecord creation
    record = FeedbackRecord(
        message_id="msg-123",
        session_id="sess-456",
        question="Show me all products",
        sql="SELECT * FROM products",
        feedback_type=FeedbackType.THUMBS_UP
    )
    assert record.id is not None
    assert record.feedback_type == FeedbackType.THUMBS_UP
    print("  [OK] FeedbackRecord creation works")
    
    # Test FeedbackRequest
    request = FeedbackRequest(
        message_id="msg-123",
        session_id="sess-456",
        feedback_type=FeedbackType.THUMBS_DOWN,
        reason="Wrong table used"
    )
    assert request.reason == "Wrong table used"
    print("  [OK] FeedbackRequest creation works")
    
    # Test PolicyHint
    hint = PolicyHint(
        hint_type="caution",
        description="Be careful with products table",
        weight=0.8,
        tables=["products"]
    )
    assert hint.weight == 0.8
    print("  [OK] PolicyHint creation works")
    
    print("[PASS] All feedback model tests passed!\n")


def test_rlhf_store():
    """Test RLHF JSON store."""
    print("Testing RLHF store...")
    
    # Create temp directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        store = RLHFStore(storage_dir=temp_dir)
        
        # Test saving feedback
        record1 = FeedbackRecord(
            message_id="msg-1",
            session_id="sess-1",
            question="Show me all orders",
            sql="SELECT * FROM orders",
            feedback_type=FeedbackType.THUMBS_UP,
            metadata={"tables": ["orders"], "patterns": ["SELECT"]}
        )
        store.save_feedback(record1)
        print("  [OK] Feedback saved successfully")
        
        # Test loading feedback
        all_feedback = store.get_all_feedback()
        assert len(all_feedback) == 1
        assert all_feedback[0].message_id == "msg-1"
        print("  [OK] Feedback loaded successfully")
        
        # Add more feedback for stats
        record2 = FeedbackRecord(
            message_id="msg-2",
            session_id="sess-1",
            question="Show me customer orders",
            sql="SELECT * FROM customers JOIN orders ON ...",
            feedback_type=FeedbackType.THUMBS_DOWN,
            metadata={"tables": ["customers", "orders"], "patterns": ["JOIN"]}
        )
        store.save_feedback(record2)
        
        # Test stats
        stats = store.get_aggregated_stats()
        assert stats.total_feedback == 2
        assert stats.thumbs_up_count == 1
        assert stats.thumbs_down_count == 1
        assert stats.success_rate == 0.5
        print(f"  [OK] Stats calculated correctly: {stats.success_rate:.0%} success rate")
        
        # Test table filtering
        orders_feedback = store.get_feedback_for_tables(["orders"])
        assert len(orders_feedback) == 2
        print("  [OK] Table filtering works")
        
        # Test policy hints
        hint = PolicyHint(
            hint_type="caution",
            description="JOIN with customers table often fails",
            weight=0.7,
            tables=["customers"]
        )
        store.add_policy_hint(hint)
        
        hints = store.get_hints_for_context(["customers"])
        assert len(hints) == 1
        print("  [OK] Policy hints stored and retrieved")
        
        # Verify file persistence
        assert (Path(temp_dir) / "feedback_records.json").exists()
        assert (Path(temp_dir) / "policy_state.json").exists()
        print("  [OK] Data persisted to JSON files")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("[PASS] All RLHF store tests passed!\n")


def test_policy_engine():
    """Test policy engine functionality."""
    print("Testing policy engine...")
    
    # Create temp directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        store = RLHFStore(storage_dir=temp_dir)
        engine = PolicyEngine(store=store)
        
        # Test SQL table extraction
        tables = engine.extract_tables_from_sql(
            "SELECT * FROM products JOIN orders ON products.id = orders.product_id"
        )
        assert "products" in tables
        assert "orders" in tables
        print(f"  [OK] Table extraction: {tables}")
        
        # Test SQL pattern extraction
        patterns = engine.extract_sql_patterns(
            "SELECT COUNT(*) FROM products GROUP BY category"
        )
        assert "COUNT" in patterns
        assert "GROUP BY" in patterns
        print(f"  [OK] Pattern extraction: {patterns}")
        
        # Test recording feedback
        record = engine.record_feedback(
            message_id="test-msg-1",
            session_id="test-sess-1",
            question="How many products per category?",
            sql="SELECT category, COUNT(*) FROM products GROUP BY category",
            feedback_type=FeedbackType.THUMBS_UP
        )
        assert record.id is not None
        print("  [OK] Feedback recorded via engine")
        
        # Record negative feedback to trigger policy hints
        for i in range(3):  # Need multiple to trigger hints
            engine.record_feedback(
                message_id=f"test-msg-neg-{i}",
                session_id="test-sess-1",
                question="Complex query about customers",
                sql="SELECT * FROM customers JOIN orders ON customers.id = orders.customer_id",
                feedback_type=FeedbackType.THUMBS_DOWN,
                reason="Wrong results" if i == 0 else None
            )
        print("  [OK] Multiple negative feedback recorded")
        
        # Get policy hints
        hints = engine.get_policy_hints(
            question="Show me customer data",
            tables=["customers", "orders"]
        )
        print(f"  [OK] Retrieved {len(hints)} policy hints")
        
        # Test prompt formatting
        if hints:
            formatted = engine.format_hints_for_prompt(hints)
            assert "BASED ON PREVIOUS USER FEEDBACK" in formatted
            print(f"  [OK] Hints formatted for prompt")
        
        # Get stats
        stats = engine.get_feedback_stats()
        assert stats.total_feedback > 0
        print(f"  [OK] Stats: {stats.total_feedback} feedback, {stats.success_rate:.0%} success rate")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("[PASS] All policy engine tests passed!\n")


def test_serialization():
    """Test JSON serialization for API responses."""
    print("Testing serialization...")
    
    # Test FeedbackStats serialization
    stats = FeedbackStats(
        total_feedback=10,
        thumbs_up_count=7,
        thumbs_down_count=3,
        success_rate=0.7,
        feedback_by_table={"products": {"thumbs_up": 5, "thumbs_down": 2}},
        active_hints=3
    )
    json_str = stats.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["total_feedback"] == 10
    print("  [OK] FeedbackStats serializes correctly")
    
    # Test PolicyHint serialization
    hint = PolicyHint(
        hint_type="prefer",
        description="Use COALESCE for nullable columns",
        weight=0.85,
        tables=["products", "orders"]
    )
    json_str = hint.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["hint_type"] == "prefer"
    print("  [OK] PolicyHint serializes correctly")
    
    print("[PASS] All serialization tests passed!\n")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RLHF Implementation Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_feedback_models()
        test_rlhf_store()
        test_policy_engine()
        test_serialization()
        
        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
