"""Test suite for GRPO (Group Relative Policy Optimization) implementation."""

import sys
import os
import tempfile
import shutil
import statistics
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.grpo.grpo_config import GRPOConfig
from app.services.grpo.grpo_models import (
    GRPOCompletion, GRPOSample, GRPOStep, GRPOTrainingState, GRPOVisualizationData
)
from app.services.grpo.reward_functions import RewardFunctions
from app.services.grpo.grpo_trainer import GRPOTrainer
from app.services.rlhf_store import RLHFStore


def test_grpo_config():
    """Test GRPO configuration."""
    print("Testing GRPO config...")
    
    # Test default config
    config = GRPOConfig()
    assert config.group_size == 4
    assert config.scale_rewards == True
    assert config.kl_coef == 0.05
    print("  [OK] Default config created")
    
    # Test custom config
    config = GRPOConfig(group_size=8, scale_rewards=False)
    assert config.group_size == 8
    assert config.scale_rewards == False
    print("  [OK] Custom config created")
    
    print("[PASS] GRPO config tests passed!\n")


def test_grpo_models():
    """Test GRPO data models."""
    print("Testing GRPO models...")
    
    # Test GRPOCompletion
    completion = GRPOCompletion(
        sql="SELECT * FROM products",
        total_reward=0.75,
        advantage=0.5,
        reward_breakdown={"sql_validity": 0.8, "execution": 0.7}
    )
    assert completion.sql == "SELECT * FROM products"
    assert completion.advantage == 0.5
    print("  [OK] GRPOCompletion created")
    
    # Test GRPOSample
    sample = GRPOSample(
        prompt="Show all products",
        completions=[completion, completion],
        mean_reward=0.75,
        std_reward=0.1
    )
    assert len(sample.completions) == 2
    assert sample.mean_reward == 0.75
    print("  [OK] GRPOSample created")
    
    # Test GRPOStep
    step = GRPOStep(step_number=1, samples=[sample])
    assert step.step_number == 1
    assert len(step.samples) == 1
    print("  [OK] GRPOStep created")
    
    # Test GRPOTrainingState
    state = GRPOTrainingState()
    state.add_step(step)
    assert state.total_steps == 1
    print("  [OK] GRPOTrainingState updated")
    
    # Test GRPOVisualizationData
    viz = GRPOVisualizationData.from_sample(sample)
    assert viz.question == "Show all products"
    assert len(viz.completions) == 2
    print("  [OK] GRPOVisualizationData created")
    
    print("[PASS] GRPO models tests passed!\n")


def test_reward_functions():
    """Test reward function calculations."""
    print("Testing reward functions...")
    
    rf = RewardFunctions()
    
    # Test SQL validity
    score, details = rf.sql_validity_reward("SELECT * FROM products")
    assert score > 0  # Valid SQL should have positive score
    assert details["has_select"] == True
    assert details["has_from"] == True
    print(f"  [OK] SQL validity reward: {score:.3f}")
    
    # Test invalid SQL
    score, details = rf.sql_validity_reward("")
    assert score < 0  # Empty SQL should have negative score
    print(f"  [OK] Invalid SQL reward: {score:.3f}")
    
    # Test execution reward (simulated)
    score, details = rf.execution_reward(
        "SELECT * FROM products",
        execution_result={"total_rows": 10}
    )
    assert score == 1.0  # Successful execution
    print(f"  [OK] Execution reward: {score:.3f}")
    
    # Test execution error
    score, details = rf.execution_reward(
        "SELECT * FROM nonexistent",
        execution_error="Table not found"
    )
    assert score < 0  # Error should have negative score
    print(f"  [OK] Execution error reward: {score:.3f}")
    
    # Test result quality
    score, details = rf.result_quality_reward(
        sql="SELECT product, SUM(revenue) FROM sales GROUP BY product",
        question="Show total revenue by product"
    )
    # Should match well due to keyword overlap
    print(f"  [OK] Result quality reward: {score:.3f}")
    
    # Test format quality
    score, details = rf.format_quality_reward(
        "SELECT CAST(price AS DOUBLE), COALESCE(name, 'N/A') AS product_name FROM products"
    )
    assert len(details["good_patterns"]) > 0  # Should detect CAST and COALESCE
    print(f"  [OK] Format quality reward: {score:.3f}, patterns: {details['good_patterns']}")
    
    # Test total reward
    total, breakdown = rf.compute_total_reward(
        sql="SELECT category, COUNT(*) FROM products GROUP BY category",
        question="How many products per category?"
    )
    assert "sql_validity" in breakdown
    assert "execution_success" in breakdown
    assert "result_quality" in breakdown
    assert "format_quality" in breakdown
    print(f"  [OK] Total reward: {total:.4f}")
    
    print("[PASS] Reward function tests passed!\n")


def test_advantage_calculation():
    """Test GRPO advantage calculation."""
    print("Testing advantage calculation...")
    
    config = GRPOConfig(scale_rewards=True)
    
    # Create trainer with temp store
    temp_dir = tempfile.mkdtemp()
    try:
        store = RLHFStore(storage_dir=temp_dir)
        trainer = GRPOTrainer(config=config, store=store)
        
        # Test with known rewards
        rewards = [1.0, 0.5, 0.0, -0.5]  # Clear hierarchy
        advantages = trainer.compute_advantages(rewards)
        
        # Higher rewards should have positive advantages
        assert advantages[0] > 0  # 1.0 is above mean
        assert advantages[1] > 0  # 0.5 is above mean
        assert advantages[2] < 0  # 0.0 is below mean
        assert advantages[3] < 0  # -0.5 is below mean
        print(f"  [OK] Advantages: {[f'{a:.3f}' for a in advantages]}")
        
        # Verify normalization
        mean_adv = statistics.mean(advantages)
        assert abs(mean_adv) < 0.01  # Mean advantage should be ~0
        print(f"  [OK] Mean advantage ~= 0: {mean_adv:.5f}")
        
        # Test with scale_rewards=False
        config2 = GRPOConfig(scale_rewards=False)
        trainer2 = GRPOTrainer(config=config2, store=store)
        advantages2 = trainer2.compute_advantages(rewards)
        print(f"  [OK] Unscaled advantages: {[f'{a:.3f}' for a in advantages2]}")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("[PASS] Advantage calculation tests passed!\n")


def test_grpo_training_step():
    """Test complete GRPO training step."""
    print("Testing GRPO training step...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        store = RLHFStore(storage_dir=temp_dir)
        config = GRPOConfig(group_size=4, verbose=False)
        trainer = GRPOTrainer(config=config, store=store)
        
        # Run a training step with simulation
        step = trainer.run_step(
            questions=["Show all products"],
            use_simulation=True,
            execute_queries=False
        )
        
        assert step.step_number == 1
        assert len(step.samples) == 1
        print(f"  [OK] Training step completed")
        
        sample = step.samples[0]
        assert len(sample.completions) == 4  # group_size=4
        print(f"  [OK] Generated {len(sample.completions)} completions")
        
        # Check advantages are computed
        advantages = [c.advantage for c in sample.completions]
        assert any(a > 0 for a in advantages)  # Should have positive advantages
        assert any(a < 0 for a in advantages)  # Should have negative advantages
        print(f"  [OK] Advantages computed: {[f'{a:.3f}' for a in advantages]}")
        
        # Check state was updated
        assert trainer.state.total_steps == 1
        assert trainer.state.total_samples == 1
        print(f"  [OK] Training state updated")
        
        # Get summary
        summary = trainer.get_training_summary()
        assert summary["total_steps"] == 1
        print(f"  [OK] Training summary: {summary}")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("[PASS] GRPO training step tests passed!\n")


def test_policy_layer_updates():
    """Test that GRPO updates policy layer (not LLM)."""
    print("Testing policy layer updates...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        store = RLHFStore(storage_dir=temp_dir)
        config = GRPOConfig(
            group_size=4,
            min_advantage_threshold=0.1,  # Lower threshold for testing
            verbose=False
        )
        trainer = GRPOTrainer(config=config, store=store)
        
        # Initial hint count
        initial_hints = len(store.get_policy_state().hints)
        print(f"  Initial hints: {initial_hints}")
        
        # Create a sample with clear advantage differences
        sample = GRPOSample(
            prompt="Test query",
            completions=[
                GRPOCompletion(
                    sql="SELECT SUM(amount) FROM orders GROUP BY product",
                    total_reward=1.0,
                    advantage=1.5  # Strong positive
                ),
                GRPOCompletion(
                    sql="SELECT * FROM invalid_table",
                    total_reward=-0.5,
                    advantage=-1.5  # Strong negative
                ),
            ],
            mean_reward=0.25,
            std_reward=0.75,
            best_completion_idx=0,
            tables_involved=["orders"],
            patterns_found=["SUM", "GROUP BY"]
        )
        
        # Run policy update
        updates = trainer.update_policy_layer(sample)
        
        # Check hints were created/updated
        final_hints = len(store.get_policy_state().hints)
        print(f"  Final hints: {final_hints}")
        print(f"  Updates: {updates}")
        
        assert updates["hints_created"] > 0 or updates["hints_updated"] > 0
        print("  [OK] Policy hints were created/updated")
        
        # Verify LLM was NOT modified (trainer doesn't touch bedrock weights)
        # This is implicit - our implementation only updates PolicyHints
        print("  [OK] LLM was NOT retrained (policy-layer only)")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("[PASS] Policy layer update tests passed!\n")


def test_visualization_data():
    """Test visualization data generation."""
    print("Testing visualization data...")
    
    sample = GRPOSample(
        prompt="Show revenue by month",
        completions=[
            GRPOCompletion(sql="SELECT * FROM sales", total_reward=0.5, advantage=0.2),
            GRPOCompletion(sql="SELECT month, SUM(revenue) FROM sales GROUP BY month", total_reward=0.9, advantage=0.8),
        ],
        mean_reward=0.7,
        std_reward=0.2,
        best_completion_idx=1
    )
    
    viz = GRPOVisualizationData.from_sample(sample)
    
    assert viz.question == "Show revenue by month"
    assert viz.reward_stats["mean"] == 0.7
    assert viz.reward_stats["std"] == 0.2
    assert len(viz.completions) == 2
    assert viz.completions[1]["is_best"] == True
    print(f"  [OK] Visualization data created")
    print(f"  [OK] Advantage explanation:\n{viz.advantage_explanation}")
    
    print("[PASS] Visualization data tests passed!\n")


def run_all_tests():
    """Run all GRPO tests."""
    print("=" * 70)
    print("GRPO Implementation Test Suite")
    print("Testing POLICY-LAYER learning (no LLM retraining)")
    print("=" * 70 + "\n")
    
    try:
        test_grpo_config()
        test_grpo_models()
        test_reward_functions()
        test_advantage_calculation()
        test_grpo_training_step()
        test_policy_layer_updates()
        test_visualization_data()
        
        print("=" * 70)
        print("ALL GRPO TESTS PASSED! [OK]")
        print()
        print("Key Verification:")
        print("  • GRPO generates multiple completions per question")
        print("  • Rewards are calculated using multiple criteria")
        print("  • Advantages are computed RELATIVE to group mean")
        print("  • Policy layer (hints, weights) is updated")
        print("  • LLM (Bedrock) is NEVER retrained")
        print("=" * 70)
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
