# GRPO: Group Relative Policy Optimization for Text-to-SQL

## Introduction

**GRPO (Group Relative Policy Optimization)** is an advanced reinforcement learning technique that improves AI response quality through comparative learning. Originally introduced by DeepSeek for mathematical reasoning, GRPO is particularly effective for tasks like Text-to-SQL where patterns repeat and feedback is sparse.

### The Key Insight

Traditional RLHF (Reinforcement Learning from Human Feedback) evaluates each response independently. GRPO takes a different approach: **generate multiple responses and compare them within the group**.

```
Traditional RLHF: "Is this response good?" → Score it
GRPO:            "Which response is best?" → Compare within group
```

This group-relative comparison provides more stable learning signals and eliminates the need for a separate reward model or critic network.

---

## What Makes GRPO Different

### GRPO is Policy-Layer Learning

A critical distinction that's often misunderstood:

| Approach | What Gets Modified | Infrastructure Required |
|----------|-------------------|------------------------|
| Full Fine-tuning | LLM weights | GPUs, training pipeline |
| RLHF with PPO | Reward model + LLM | Complex, expensive |
| **GRPO (Policy-Layer)** | **Policy hints, weights** | **Minimal, safe** |

**GRPO does not require retraining the base LLM.** Instead, it updates:
- Policy hint weights
- Pattern preferences  
- System prompt guidance
- Scoring calibrations

This makes GRPO ideal for enterprise environments where model stability and auditability are paramount.

---

## How GRPO Works: Step-by-Step

### Step 1: Generate Multiple Responses (Group Sampling)

For each user query, generate **G** different responses instead of just one. In our implementation, G=4 by default.

```python
# Configuration
config = GRPOConfig(group_size=4)

# For the question "Show total revenue by product"
# Generate 4 different SQL queries
completions = [
    "SELECT product, SUM(revenue) FROM sales GROUP BY product",
    "SELECT p.name, SUM(amount) FROM products p JOIN orders o...",
    "SELECT productname, total_revenue FROM revenue_summary",
    "SELECT product_id, COUNT(*) FROM orders GROUP BY product_id"
]
```

**Why multiple responses?** Different responses have different quality levels. By generating several, we can learn which approaches work better.

### Step 2: Score Each Response (Reward Functions)

Each completion is evaluated by multiple reward functions:

| Reward Function | Weight | What It Measures |
|----------------|--------|------------------|
| SQL Validity | 20% | Syntax correctness, proper structure |
| Execution Success | 30% | Whether the query runs successfully |
| Result Quality | 35% | Relevance to the original question |
| Format Quality | 15% | Best practices (aliasing, type casting) |

**Example scoring:**

```
Question: "Show total revenue by product"

Completion 1: SELECT product, SUM(revenue) FROM sales GROUP BY product
  - Validity: +1.0, Execution: 0.0, Quality: +0.4, Format: +0.6
  - Total Reward: +0.414

Completion 2: SELECT p.name, SUM(amount) FROM products p JOIN orders o...
  - Validity: +1.0, Execution: 0.0, Quality: +0.5, Format: +1.0
  - Total Reward: +0.497

Completion 3: SELECT productname FROM revenue_summary (wrong table)
  - Validity: +1.0, Execution: 0.0, Quality: -0.1, Format: 0.0
  - Total Reward: +0.190

Completion 4: SELECT product_id, COUNT(*) FROM orders (wrong metric)
  - Validity: +1.0, Execution: 0.0, Quality: +0.2, Format: +0.6
  - Total Reward: +0.340
```

### Step 3: Compute Group-Relative Advantages

This is the **core innovation of GRPO**. Instead of using absolute reward scores, we calculate how each response performs relative to the group average.

**The GRPO Formula:**

```
Advantage = (reward - mean) / std
```

**Example calculation:**

```python
rewards = [0.414, 0.497, 0.190, 0.340]

mean = 0.360
std  = 0.127

Advantages:
  Completion 1: (0.414 - 0.360) / 0.127 = +0.425  → REINFORCE
  Completion 2: (0.497 - 0.360) / 0.127 = +1.079  → STRONGLY REINFORCE
  Completion 3: (0.190 - 0.360) / 0.127 = -1.339  → PENALIZE
  Completion 4: (0.340 - 0.360) / 0.127 = -0.157  → SLIGHTLY PENALIZE
```

**Interpretation:**
- **Positive advantage**: Response is above group average → increase likelihood
- **Negative advantage**: Response is below group average → decrease likelihood
- **Magnitude**: How strongly to reinforce/penalize

### Step 4: Update Policy Layer

Based on the computed advantages, update the policy layer (not the LLM):

```python
# Patterns from high-advantage completions get reinforced
patterns_reinforced = ['GROUP BY', 'SUM', 'JOIN']

# PolicyHints are created/updated
{
    "hint_type": "prefer",
    "description": "Pattern 'SUM' performed well (advantage: +1.08)",
    "weight": 0.85,
    "tables": ["products", "orders"],
    "pattern": "SUM"
}
```

The updated PolicyHints are then injected into future SQL generation prompts, guiding the LLM toward better patterns.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GRPO Pipeline                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │  User    │───►│ Group Sampler │───►│  Reward Functions   │   │
│  │ Question │    │ (G=4 SQLs)    │    │  (validity, exec,   │   │
│  └──────────┘    └──────────────┘    │   quality, format)  │   │
│                                       └──────────┬──────────┘   │
│                                                  │               │
│  ┌──────────────────────────────────────────────▼────────────┐  │
│  │              Advantage Calculator                          │  │
│  │         Advantage = (reward - mean) / std                  │  │
│  └──────────────────────────────────────────────┬────────────┘  │
│                                                  │               │
│  ┌──────────────────────────────────────────────▼────────────┐  │
│  │              Policy Layer Updater                          │  │
│  │  - Update PolicyHint weights                               │  │
│  │  - Reinforce successful patterns                           │  │
│  │  - Flag problematic patterns                               │  │
│  │  (LLM is NOT modified)                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Reference

The complete GRPO implementation is organized in the following modules:

### Module Structure

```
backend/app/services/grpo/
├── __init__.py           # Module exports
├── grpo_config.py        # Configuration and hyperparameters
├── grpo_models.py        # Data structures
├── reward_functions.py   # SQL evaluation functions
├── grpo_trainer.py       # Main training logic
└── grpo_demo.py          # Interactive demonstration

backend/tests/
└── test_grpo.py          # Comprehensive test suite
```

### Key Components

#### 1. GRPOConfig (grpo_config.py)

Configures the GRPO training parameters:

```python
class GRPOConfig(BaseModel):
    group_size: int = 4              # Number of completions per query
    temperature_sampling: float = 0.7 # Diversity in generation
    kl_coef: float = 0.05            # KL divergence regularization
    scale_rewards: bool = True       # Normalize by std
    learning_rate: float = 0.1       # Policy update rate
    min_advantage_threshold: float = 0.3  # Minimum advantage to trigger update
```

#### 2. RewardFunctions (reward_functions.py)

Implements the scoring logic for SQL completions:

```python
class RewardFunctions:
    def sql_validity_reward(self, sql: str) -> Tuple[float, Dict]:
        """Check SQL syntax validity (+1.0 to -1.0)"""
        
    def execution_reward(self, sql: str, result: Dict) -> Tuple[float, Dict]:
        """Score based on execution success"""
        
    def result_quality_reward(self, sql: str, question: str) -> Tuple[float, Dict]:
        """Evaluate relevance to the question"""
        
    def format_quality_reward(self, sql: str) -> Tuple[float, Dict]:
        """Assess SQL best practices"""
        
    def compute_total_reward(self, sql: str, question: str) -> Tuple[float, Dict]:
        """Combine all rewards with configurable weights"""
```

#### 3. GRPOTrainer (grpo_trainer.py)

The main training loop implementing all GRPO stages:

```python
class GRPOTrainer:
    def generate_group(self, question: str, num_samples: int) -> List[str]:
        """STEP 1: Generate G completions"""
        
    def compute_rewards(self, completions: List[str], question: str) -> List[Tuple]:
        """STEP 2: Score each completion"""
        
    def compute_advantages(self, rewards: List[float]) -> List[float]:
        """STEP 3: Calculate group-relative advantages"""
        
    def update_policy_layer(self, sample: GRPOSample) -> Dict:
        """STEP 4: Update PolicyHints based on advantages"""
        
    def run_step(self, questions: List[str]) -> GRPOStep:
        """Execute complete training step"""
```

---

## Usage Examples

### Basic Training Step

```python
from app.services.grpo import GRPOTrainer, GRPOConfig

# Initialize
config = GRPOConfig(group_size=4, verbose=True)
trainer = GRPOTrainer(config=config)

# Run a training step
step = trainer.run_step(
    questions=["Show total revenue by product", "List all customers"],
    use_simulation=True  # Use existing feedback data
)

# View results
print(f"Samples processed: {len(step.samples)}")
print(f"Hints created: {step.hints_created}")
print(f"Hints updated: {step.hints_updated}")

for sample in step.samples:
    print(f"\nQuestion: {sample.prompt}")
    for i, c in enumerate(sample.completions):
        status = "REINFORCE" if c.advantage > 0 else "PENALIZE"
        print(f"  SQL {i+1}: advantage={c.advantage:+.3f} → {status}")
```

### Viewing Training Progress

```python
# Get training summary
summary = trainer.get_training_summary()

print(f"Total steps: {summary['total_steps']}")
print(f"Average reward: {summary['avg_reward']}")
print(f"Hints created: {summary['hints_created']}")
```

### Integration with Existing RLHF Store

The GRPO implementation integrates with the existing feedback storage:

```python
from app.services.rlhf_store import get_rlhf_store
from app.services.grpo import GRPOTrainer

# Use existing feedback data
store = get_rlhf_store()
trainer = GRPOTrainer(store=store)

# Existing feedback informs GRPO training
existing_feedback = store.get_all_feedback()
print(f"Training with {len(existing_feedback)} feedback records")
```

---

## Test Results

The implementation includes a comprehensive test suite that validates all components:

```
======================================================================
GRPO Implementation Test Suite
Testing POLICY-LAYER learning (no LLM retraining)
======================================================================

[PASS] GRPO config tests
[PASS] GRPO models tests  
[PASS] Reward function tests
[PASS] Advantage calculation tests
[PASS] GRPO training step tests
[PASS] Policy layer update tests
[PASS] Visualization data tests

Key Verification:
  • GRPO generates multiple completions per question
  • Rewards are calculated using multiple criteria
  • Advantages are computed RELATIVE to group mean
  • Policy layer (hints, weights) is updated
  • LLM (Bedrock) is NEVER retrained

ALL GRPO TESTS PASSED!
======================================================================
```

---

## When to Use GRPO

GRPO is particularly effective when:

1. **Feedback is sparse** - You don't have millions of labeled examples
2. **Patterns repeat** - Similar query types appear regularly
3. **Trust matters** - Predictable, auditable behavior is important
4. **Model access is limited** - You can't retrain the base LLM

This makes GRPO ideal for:
- Text-to-SQL systems
- RAG (Retrieval Augmented Generation)
- Tool-using agents
- Enterprise AI applications

---

## Key Takeaways

1. **GRPO generates multiple responses** (G=4) and compares them within the group

2. **The advantage formula is the core**: `Advantage = (reward - mean) / std`

3. **Policy layer gets updated**, not the LLM - making it safe for production

4. **Patterns are reinforced or penalized** based on their relative performance

5. **Integration is seamless** - works with existing feedback storage and LLM services

---

## References

- DeepSeekMath Paper: [Pushing the Limits of Mathematical Reasoning in Open Language Models](https://arxiv.org/abs/2402.03300)
- Hugging Face TRL: [GRPO Trainer Documentation](https://huggingface.co/docs/trl/grpo_trainer)
- This Implementation: `backend/app/services/grpo/`
