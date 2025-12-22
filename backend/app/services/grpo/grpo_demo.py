#!/usr/bin/env python3
"""
GRPO Demo Script - Step-by-Step Demonstration for LinkedIn Content.

This script demonstrates GRPO (Group Relative Policy Optimization) in action
using your existing ClearSky Text-to-SQL chatbot data.

IMPORTANT: This is POLICY-LAYER learning, not LLM retraining!

Run this script to see:
1. Group sampling - Generate multiple SQL responses
2. Reward calculation - Score each response
3. Advantage computation - The GRPO magic formula
4. Policy updates - How hints get created/updated

Usage:
    cd d:\\antigravity\\clearskychatbot\\backend
    python -m app.services.grpo.grpo_demo
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.services.grpo.grpo_config import GRPOConfig
from app.services.grpo.grpo_trainer import GRPOTrainer
from app.services.grpo.grpo_models import GRPOVisualizationData
from app.services.rlhf_store import RLHFStore

# Configure logging for nice output
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    line = char * 70
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


def print_step(step_num: int, title: str):
    """Print a step marker."""
    print(f"\n{'─' * 70}")
    print(f"  📌 STEP {step_num}: {title}")
    print(f"{'─' * 70}\n")


def print_completion_table(completions: list):
    """Print completions in a table format."""
    print("  ┌────┬──────────┬───────────┬────────────────────────────────────────┐")
    print("  │ #  │ Reward   │ Advantage │ SQL (truncated)                        │")
    print("  ├────┼──────────┼───────────┼────────────────────────────────────────┤")
    
    for c in completions:
        idx = c.get("index", 0)
        reward = c.get("total_reward", 0)
        adv = c.get("advantage", 0)
        sql = c.get("sql", "")[:38]
        
        status = "✅" if c.get("is_best") else "  "
        adv_sign = "+" if adv > 0 else ""
        
        print(f"  │ {status}{idx} │ {reward:+.3f}   │ {adv_sign}{adv:.3f}    │ {sql:<38} │")
    
    print("  └────┴──────────┴───────────┴────────────────────────────────────────┘")


def print_advantage_explanation(mean: float, std: float, completions: list):
    """Print the advantage calculation explanation."""
    print("  GRPO FORMULA:")
    print(f"  Advantage = (reward - mean) / std")
    print(f"            = (reward - {mean:.3f}) / {std:.3f}")
    print()
    print("  INTERPRETATION:")
    
    for c in completions:
        adv = c.get("advantage", 0)
        idx = c.get("index", 0)
        
        if adv > 0.5:
            print(f"    Completion {idx}: {adv:+.3f} → 🟢 STRONGLY REINFORCE (well above average)")
        elif adv > 0:
            print(f"    Completion {idx}: {adv:+.3f} → 🟡 REINFORCE (above average)")
        elif adv > -0.5:
            print(f"    Completion {idx}: {adv:+.3f} → 🟠 PENALIZE (below average)")
        else:
            print(f"    Completion {idx}: {adv:+.3f} → 🔴 STRONGLY PENALIZE (well below average)")


def run_step_by_step_demo():
    """Run the full GRPO demonstration step by step."""
    
    print_header("🚀 GRPO (Group Relative Policy Optimization) Demo")
    print("  This demonstrates POLICY-LAYER learning for Text-to-SQL")
    print("  The base LLM (AWS Bedrock) is NOT being retrained!")
    print()
    print("  As the saying goes:")
    print('    "RLHF tweaks responses. GRPO shapes behavior."')
    print()
    
    # Initialize
    print_header("📋 Initialization", "─")
    
    config = GRPOConfig(
        group_size=4,
        verbose=False,
        scale_rewards=True
    )
    print(f"  Group Size (G): {config.group_size}")
    print(f"  Scale Rewards: {config.scale_rewards}")
    print(f"  Learning Rate: {config.learning_rate}")
    print()
    
    # Create trainer with existing RLHF store
    store = RLHFStore()
    trainer = GRPOTrainer(config=config, store=store)
    
    # Check existing feedback
    existing_feedback = store.get_all_feedback()
    print(f"  📊 Found {len(existing_feedback)} existing feedback records")
    
    if existing_feedback:
        print(f"  📝 Sample questions from feedback:")
        for i, f in enumerate(existing_feedback[:3]):
            print(f"      {i+1}. {f.question}")
    
    # =========================================================================
    # STEP 1: Generate Group of Completions
    # =========================================================================
    print_step(1, "GENERATE GROUP OF COMPLETIONS")
    
    print("  💡 Instead of generating ONE SQL query, we generate G queries.")
    print("  💡 This allows us to COMPARE responses within the group.")
    print()
    
    # Get a question to process
    if existing_feedback:
        test_question = existing_feedback[0].question
        expected_tables = existing_feedback[0].metadata.get("tables", [])
    else:
        test_question = "Show total revenue by product"
        expected_tables = ["products", "orders"]
    
    print(f"  Question: \"{test_question}\"")
    print(f"  Expected Tables: {expected_tables}")
    print()
    
    # Generate completions (simulated from existing data)
    completions = trainer.generate_group_simulated(
        test_question,
        [f.model_dump() for f in existing_feedback] if existing_feedback else None
    )
    
    print(f"  Generated {len(completions)} SQL completions:")
    for i, sql in enumerate(completions):
        print(f"\n  📄 Completion {i+1}:")
        print(f"     {sql[:100]}{'...' if len(sql) > 100 else ''}")
    
    # =========================================================================
    # STEP 2: Compute Rewards
    # =========================================================================
    print_step(2, "COMPUTE REWARDS")
    
    print("  💡 Each completion is scored by multiple reward functions:")
    print("      • SQL Validity (syntax check)")
    print("      • Execution Success (can it run?)")
    print("      • Result Quality (does it answer the question?)")
    print("      • Format Quality (best practices)")
    print()
    
    reward_results = trainer.compute_rewards(
        completions=completions,
        question=test_question,
        expected_tables=expected_tables,
        execute_queries=False  # Simulation mode
    )
    
    print("  📊 Reward Breakdown:")
    print("  ┌────┬────────────┬────────────┬────────────┬────────────┬─────────┐")
    print("  │ #  │ Validity   │ Execution  │ Quality    │ Format     │ TOTAL   │")
    print("  ├────┼────────────┼────────────┼────────────┼────────────┼─────────┤")
    
    for i, (total, breakdown) in enumerate(reward_results):
        v = breakdown.get("sql_validity", {}).get("score", 0)
        e = breakdown.get("execution_success", {}).get("score", 0)
        q = breakdown.get("result_quality", {}).get("score", 0)
        f = breakdown.get("format_quality", {}).get("score", 0)
        print(f"  │ {i+1}  │ {v:+.3f}     │ {e:+.3f}     │ {q:+.3f}     │ {f:+.3f}     │ {total:+.4f} │")
    
    print("  └────┴────────────┴────────────┴────────────┴────────────┴─────────┘")
    
    # =========================================================================
    # STEP 3: Compute Group-Relative Advantages (THE GRPO MAGIC!)
    # =========================================================================
    print_step(3, "COMPUTE GROUP-RELATIVE ADVANTAGES ⭐")
    
    print("  💡 THIS IS THE CORE OF GRPO!")
    print("  💡 Instead of absolute scores, we compare WITHIN THE GROUP.")
    print()
    
    rewards = [r[0] for r in reward_results]
    advantages = trainer.compute_advantages(rewards)
    
    import statistics
    mean_reward = statistics.mean(rewards)
    std_reward = statistics.stdev(rewards) if len(rewards) > 1 else 1.0
    
    print(f"  Group Statistics:")
    print(f"    • Mean Reward: {mean_reward:.4f}")
    print(f"    • Std Deviation: {std_reward:.4f}")
    print()
    
    completions_data = [
        {
            "index": i+1,
            "sql": completions[i],
            "total_reward": rewards[i],
            "advantage": advantages[i],
            "is_best": rewards[i] == max(rewards)
        }
        for i in range(len(completions))
    ]
    
    print_completion_table(completions_data)
    print()
    print_advantage_explanation(mean_reward, std_reward, completions_data)
    
    # =========================================================================
    # STEP 4: Update Policy Layer (NOT the LLM!)
    # =========================================================================
    print_step(4, "UPDATE POLICY LAYER")
    
    print("  💡 We update the POLICY LAYER, not the LLM!")
    print("  💡 This includes:")
    print("      • PolicyHint weights")
    print("      • Pattern preferences")
    print("      • System prompt improvements")
    print()
    print("  ⚠️  The base LLM (AWS Bedrock) remains UNCHANGED!")
    print()
    
    # Create a GRPO sample for policy update
    from app.services.grpo.grpo_models import GRPOSample, GRPOCompletion
    
    sample = GRPOSample(
        prompt=test_question,
        completions=[
            GRPOCompletion(
                sql=completions[i],
                total_reward=rewards[i],
                advantage=advantages[i]
            )
            for i in range(len(completions))
        ],
        mean_reward=mean_reward,
        std_reward=std_reward,
        best_completion_idx=rewards.index(max(rewards)),
        tables_involved=expected_tables,
        patterns_found=trainer.policy_engine.extract_sql_patterns(
            completions[rewards.index(max(rewards))]
        )
    )
    
    # Perform policy update
    updates = trainer.update_policy_layer(sample)
    
    print("  📝 Policy Layer Updates:")
    print(f"      • Hints Created: {updates['hints_created']}")
    print(f"      • Hints Updated: {updates['hints_updated']}")
    
    if updates['patterns_reinforced']:
        print(f"      • Patterns Reinforced: {', '.join(updates['patterns_reinforced'])}")
    if updates['patterns_penalized']:
        print(f"      • Patterns Penalized: {', '.join(updates['patterns_penalized'])}")
    
    # Show current policy state
    policy_state = store.get_policy_state()
    print(f"\n  📋 Current Policy State:")
    print(f"      • Total Hints: {len(policy_state.hints)}")
    print(f"      • Version: {policy_state.version}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_header("📊 GRPO DEMO SUMMARY")
    
    summary = trainer.get_training_summary()
    
    print("  What We Learned:")
    print("  ─────────────────")
    print(f"    • Processed {summary['total_samples']} samples")
    print(f"    • Generated {summary['total_completions']} completions")
    print(f"    • Average Reward: {summary['avg_reward']}")
    print(f"    • Best Completion Rate: {summary['best_completion_rate']}")
    print()
    print("  Key Takeaways for LinkedIn:")
    print("  ────────────────────────────")
    print("    1. GRPO generates MULTIPLE responses (Group = G)")
    print("    2. Rewards are compared WITHIN the group (Relative)")
    print("    3. Policy layer gets updated (Policy Optimization)")
    print("    4. The LLM is NEVER fine-tuned")
    print()
    print("  \"RLHF tweaks responses. GRPO shapes behavior.\"")
    print("  \"Neither requires retraining the LLM by default.\"")
    print()
    
    print_header("✅ DEMO COMPLETE")
    
    return trainer


def run_mini_demo():
    """Run a quick mini demo with just the essentials."""
    print_header("⚡ GRPO Quick Demo", "─")
    
    config = GRPOConfig(group_size=4, verbose=False)
    trainer = GRPOTrainer(config=config)
    
    # Run demo and get visualization data
    viz_data = trainer.run_demo(num_samples=2)
    
    for viz in viz_data:
        print(f"\n📌 Question: {viz.question}")
        print(f"   Mean Reward: {viz.reward_stats['mean']:.3f}")
        print(f"   Std Reward: {viz.reward_stats['std']:.3f}")
        print(f"\n   {viz.advantage_explanation}")
        print()
    
    return viz_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GRPO Demo for Text-to-SQL")
    parser.add_argument("--quick", action="store_true", help="Run quick mini demo")
    parser.add_argument("--output", type=str, help="Output file for JSON results")
    
    args = parser.parse_args()
    
    if args.quick:
        result = run_mini_demo()
    else:
        result = run_step_by_step_demo()
    
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(result.get_training_summary() if hasattr(result, 'get_training_summary') else {}, f, indent=2)
        print(f"\n📁 Results saved to: {output_path}")
