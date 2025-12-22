"""GRPO Trainer - Policy-Level Learning for Text-to-SQL.

IMPORTANT: This implements GRPO at the POLICY LAYER, not LLM retraining.

What gets "trained" in this implementation:
1. PolicyHint weights - Learn which patterns work well/poorly
2. Prompt templates - Improve system prompts based on grouped feedback
3. Scoring heuristics - Calibrate reward functions over time

The base LLM (AWS Bedrock) remains UNTOUCHED.

As the saying goes:
    "RLHF tweaks responses. GRPO shapes behavior."
    "Neither requires retraining the LLM by default."
"""

import logging
import statistics
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json

from app.services.grpo.grpo_config import GRPOConfig
from app.services.grpo.grpo_models import (
    GRPOCompletion, GRPOSample, GRPOStep, GRPOTrainingState, GRPOVisualizationData
)
from app.services.grpo.reward_functions import RewardFunctions, get_reward_functions
from app.services.rlhf_store import RLHFStore, get_rlhf_store
from app.services.policy_engine import PolicyEngine, get_policy_engine
from app.models.feedback import PolicyHint, FeedbackType

logger = logging.getLogger(__name__)


class GRPOTrainer:
    """
    GRPO Trainer for Text-to-SQL Policy Learning.
    
    This trainer implements Group Relative Policy Optimization WITHOUT
    retraining the LLM. Instead, it:
    
    1. Generates groups of SQL completions using the existing LLM
    2. Scores each completion with reward functions
    3. Computes group-relative advantages (GRPO core formula)
    4. Updates POLICY LAYER weights based on advantages
    
    The policy layer includes:
    - PolicyHint weights (increase for positive advantage patterns)
    - System prompt suggestions
    - Pattern-based rules
    
    Example usage:
        trainer = GRPOTrainer()
        
        # Run a single GRPO step
        step_result = trainer.run_step(
            questions=["Show total revenue by product"],
            group_size=4
        )
        
        # View the advantages
        for sample in step_result.samples:
            print(f"Question: {sample.prompt}")
            for i, completion in enumerate(sample.completions):
                print(f"  SQL {i+1}: advantage={completion.advantage:.2f}")
    """
    
    def __init__(
        self,
        config: Optional[GRPOConfig] = None,
        store: Optional[RLHFStore] = None,
        policy_engine: Optional[PolicyEngine] = None,
        bedrock_service = None
    ):
        self.config = config or GRPOConfig()
        self.store = store or get_rlhf_store()
        self.policy_engine = policy_engine or get_policy_engine()
        self.reward_functions = get_reward_functions(self.config)
        
        # Lazy load bedrock service
        self._bedrock_service = bedrock_service
        
        # Training state
        self.state = GRPOTrainingState(started_at=datetime.utcnow())
        
        logger.info("GRPO Trainer initialized (policy-layer learning, no LLM retraining)")
    
    @property
    def bedrock_service(self):
        """Lazy load bedrock service."""
        if self._bedrock_service is None:
            from app.services.bedrock_llm import get_bedrock_service
            self._bedrock_service = get_bedrock_service()
        return self._bedrock_service
    
    # =========================================================================
    # STEP 1: Generate Group of Completions
    # =========================================================================
    
    def generate_group(
        self,
        question: str,
        schema_context: str = "",
        num_samples: Optional[int] = None
    ) -> List[str]:
        """
        Generate G diverse SQL completions for a single question.
        
        GRPO Step 1: Instead of generating one response, we generate G.
        Higher temperature is used to ensure diversity.
        
        Args:
            question: User's natural language question
            schema_context: Database schema context
            num_samples: Number of completions (defaults to config.group_size)
            
        Returns:
            List of G SQL query strings
        """
        G = num_samples or self.config.group_size
        completions = []
        
        # Build the prompt
        prompt = self._build_sql_prompt(question, schema_context)
        
        if self.config.verbose:
            logger.info(f"Generating {G} completions for: {question[:50]}...")
        
        for i in range(G):
            try:
                # Use varying temperature for diversity
                temp = self.config.temperature_sampling + (i * 0.1)
                temp = min(temp, 1.5)  # Cap temperature
                
                sql = self.bedrock_service.generate_text(
                    prompt,
                    system_prompt="You are an expert SQL developer. Generate valid Presto SQL. Return ONLY the SQL query, no explanations.",
                    temperature=temp
                )
                
                # Clean up the SQL
                sql = self._extract_sql(sql)
                completions.append(sql)
                
            except Exception as e:
                logger.warning(f"Failed to generate completion {i+1}: {e}")
                completions.append(f"-- Error generating SQL: {str(e)}")
        
        return completions
    
    def generate_group_simulated(
        self,
        question: str,
        existing_feedback: List[Dict] = None
    ) -> List[str]:
        """
        Generate simulated completions based on existing feedback data.
        
        Used for demonstration without calling the LLM API.
        Creates varied SQL based on known patterns.
        
        Args:
            question: User's natural language question
            existing_feedback: Previous feedback records to use as basis
            
        Returns:
            List of simulated SQL completions
        """
        G = self.config.group_size
        completions = []
        
        # Check if we have existing feedback for similar questions
        if existing_feedback:
            base_sqls = [f.get("sql", "") for f in existing_feedback if f.get("sql")]
            
            for i in range(min(G, len(base_sqls))):
                completions.append(base_sqls[i])
            
            # Generate variations for remaining slots
            while len(completions) < G:
                if completions:
                    # Create variation of existing SQL
                    base = completions[0]
                    variation = self._create_sql_variation(base, len(completions))
                    completions.append(variation)
                else:
                    # No base SQL, create placeholder
                    completions.append(f"SELECT * FROM table_{len(completions) + 1}")
        else:
            # No existing feedback, create synthetic examples
            for i in range(G):
                completions.append(self._create_synthetic_sql(question, i))
        
        return completions
    
    # =========================================================================
    # STEP 2: Compute Rewards
    # =========================================================================
    
    def compute_rewards(
        self,
        completions: List[str],
        question: str,
        expected_tables: Optional[List[str]] = None,
        execute_queries: bool = False
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Score each completion using reward functions.
        
        GRPO Step 2: Apply reward functions to each of the G completions.
        
        Args:
            completions: List of SQL queries
            question: Original question
            expected_tables: Tables that should be used
            execute_queries: Whether to actually execute SQL (expensive)
            
        Returns:
            List of (total_reward, breakdown) tuples
        """
        results = []
        
        for sql in completions:
            execution_result = None
            execution_error = None
            
            if execute_queries:
                execution_result, execution_error = self._try_execute(sql)
            
            total, breakdown = self.reward_functions.compute_total_reward(
                sql=sql,
                question=question,
                execution_result=execution_result,
                execution_error=execution_error,
                expected_tables=expected_tables
            )
            
            results.append((total, breakdown))
        
        return results
    
    # =========================================================================
    # STEP 3: Compute Group-Relative Advantages
    # =========================================================================
    
    def compute_advantages(self, rewards: List[float]) -> List[float]:
        """
        Calculate group-relative advantages.
        
        GRPO Step 3 (THE CORE FORMULA):
        
            Advantage_i = (reward_i - mean(rewards)) / std(rewards)
        
        This is what gives GRPO its name: Group Relative Policy Optimization.
        
        Responses above the group mean get POSITIVE advantage (reinforce)
        Responses below the group mean get NEGATIVE advantage (penalize)
        
        Args:
            rewards: List of reward scores for the group
            
        Returns:
            List of advantage values
        """
        if len(rewards) < 2:
            return [0.0] * len(rewards)
        
        mean_reward = statistics.mean(rewards)
        
        if self.config.scale_rewards:
            std_reward = statistics.stdev(rewards)
            if std_reward == 0:
                std_reward = 1.0  # Avoid division by zero
        else:
            # Alternative: don't scale by std (avoids difficulty bias)
            std_reward = 1.0
        
        advantages = []
        for r in rewards:
            adv = (r - mean_reward) / std_reward
            
            # Clip for stability
            adv = max(-self.config.clip_advantage, min(self.config.clip_advantage, adv))
            advantages.append(round(adv, 4))
        
        return advantages
    
    # =========================================================================
    # STEP 4: Update Policy Layer (NOT the LLM!)
    # =========================================================================
    
    def update_policy_layer(
        self,
        sample: GRPOSample,
        learning_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update policy hints based on advantages.
        
        GRPO Step 4: Policy Layer Updates (NOT LLM RETRAINING)
        
        This method updates:
        1. PolicyHint weights for patterns with strong advantages
        2. Creates new hints for consistently good/bad patterns
        3. Adjusts existing hint weights based on grouped feedback
        
        The LLM (Bedrock) is NEVER modified.
        
        Args:
            sample: A GRPO sample with computed advantages
            learning_rate: Optional override for learning rate
            
        Returns:
            Dict with update statistics
        """
        lr = learning_rate or self.config.learning_rate
        updates = {
            "hints_created": 0,
            "hints_updated": 0,
            "patterns_reinforced": [],
            "patterns_penalized": []
        }
        
        # Analyze patterns from completions with positive advantages
        positive_completions = sample.get_positive_advantage_completions()
        
        for completion in positive_completions:
            if completion.advantage >= self.config.min_advantage_threshold:
                # Extract patterns from this successful SQL
                patterns = self.policy_engine.extract_sql_patterns(completion.sql)
                tables = self.policy_engine.extract_tables_from_sql(completion.sql)
                
                for pattern in patterns:
                    # Create or update a "prefer" hint
                    hint = PolicyHint(
                        hint_type="prefer",
                        description=f"Pattern '{pattern}' performed well (advantage: {completion.advantage:.2f})",
                        weight=min(1.0, 0.5 + (completion.advantage * lr)),
                        tables=tables,
                        pattern=pattern
                    )
                    self.store.add_policy_hint(hint)
                    updates["hints_updated"] += 1
                    updates["patterns_reinforced"].append(pattern)
        
        # Analyze patterns from completions with strong negative advantages
        for completion in sample.completions:
            if completion.advantage <= -self.config.min_advantage_threshold:
                patterns = self.policy_engine.extract_sql_patterns(completion.sql)
                tables = self.policy_engine.extract_tables_from_sql(completion.sql)
                
                for pattern in patterns:
                    # Create "caution" hint for problematic patterns
                    hint = PolicyHint(
                        hint_type="caution",
                        description=f"Pattern '{pattern}' underperformed (advantage: {completion.advantage:.2f})",
                        weight=min(0.9, 0.5 + abs(completion.advantage) * lr),
                        tables=tables,
                        pattern=pattern
                    )
                    self.store.add_policy_hint(hint)
                    updates["hints_created"] += 1
                    updates["patterns_penalized"].append(pattern)
        
        return updates
    
    # =========================================================================
    # Complete Training Step
    # =========================================================================
    
    def run_step(
        self,
        questions: List[str],
        schema_context: str = "",
        expected_tables: Optional[Dict[str, List[str]]] = None,
        execute_queries: bool = False,
        use_simulation: bool = True
    ) -> GRPOStep:
        """
        Run a complete GRPO training step.
        
        Combines all GRPO stages:
        1. Generate G completions per question
        2. Score with reward functions
        3. Compute group-relative advantages
        4. Update policy layer
        
        Args:
            questions: List of questions to process
            schema_context: Database schema for SQL generation
            expected_tables: Dict mapping questions to expected tables
            execute_queries: Whether to execute SQL for reward calculation
            use_simulation: Use simulated completions (faster, no API calls)
            
        Returns:
            GRPOStep with all samples and metrics
        """
        step = GRPOStep(step_number=self.state.total_steps + 1)
        all_rewards = []
        expected_tables = expected_tables or {}
        
        # Get existing feedback for simulation mode
        existing_feedback = None
        if use_simulation:
            existing_feedback = [
                r.model_dump() 
                for r in self.store.get_all_feedback()
            ]
        
        for question in questions:
            if self.config.verbose:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing: {question}")
                logger.info(f"{'='*60}")
            
            # STEP 1: Generate group
            if use_simulation:
                completions = self.generate_group_simulated(question, existing_feedback)
            else:
                completions = self.generate_group(question, schema_context)
            
            # STEP 2: Compute rewards
            tables = expected_tables.get(question, [])
            reward_results = self.compute_rewards(
                completions, question, tables, execute_queries
            )
            
            rewards = [r[0] for r in reward_results]
            all_rewards.extend(rewards)
            
            # STEP 3: Compute advantages (THE GRPO MAGIC!)
            advantages = self.compute_advantages(rewards)
            
            # Build sample with all data
            grpo_completions = []
            for i, (sql, (reward, breakdown)) in enumerate(zip(completions, reward_results)):
                comp = GRPOCompletion(
                    sql=sql,
                    reward_breakdown={k: v["score"] for k, v in breakdown.items()},
                    total_reward=reward,
                    advantage=advantages[i]
                )
                grpo_completions.append(comp)
            
            # Find best completion
            best_idx = rewards.index(max(rewards))
            
            sample = GRPOSample(
                prompt=question,
                completions=grpo_completions,
                mean_reward=statistics.mean(rewards) if rewards else 0,
                std_reward=statistics.stdev(rewards) if len(rewards) > 1 else 0,
                best_completion_idx=best_idx,
                tables_involved=tables,
                patterns_found=self.policy_engine.extract_sql_patterns(
                    completions[best_idx] if completions else ""
                )
            )
            
            # STEP 4: Update policy layer
            policy_updates = self.update_policy_layer(sample)
            step.hints_created += policy_updates["hints_created"]
            step.hints_updated += policy_updates["hints_updated"]
            
            step.samples.append(sample)
            
            if self.config.verbose:
                self._log_sample_details(sample)
        
        # Calculate step-level metrics
        if all_rewards:
            step.avg_reward = statistics.mean(all_rewards)
            
            positive_advs = [
                c.advantage for s in step.samples 
                for c in s.completions if c.advantage > 0
            ]
            negative_advs = [
                c.advantage for s in step.samples 
                for c in s.completions if c.advantage < 0
            ]
            
            if positive_advs:
                step.avg_positive_advantage = statistics.mean(positive_advs)
            if negative_advs:
                step.avg_negative_advantage = statistics.mean(negative_advs)
            
            # Best completion rate (how often top-1 is actually best)
            step.best_completion_rate = len(positive_advs) / len(all_rewards)
        
        # Update global state
        self.state.add_step(step)
        
        return step
    
    def run_demo(
        self,
        num_samples: int = 3
    ) -> List[GRPOVisualizationData]:
        """
        Run a demonstration using existing feedback data.
        
        Perfect for creating LinkedIn content!
        
        Args:
            num_samples: Number of questions to process
            
        Returns:
            List of visualization-ready data structures
        """
        # Load existing feedback
        feedback = self.store.get_all_feedback()
        
        if not feedback:
            logger.warning("No existing feedback found. Using synthetic data.")
            questions = [
                "Show total revenue by product",
                "List all customers from New York",
                "Count orders by status"
            ]
        else:
            questions = list(set(f.question for f in feedback))[:num_samples]
        
        # Get tables from feedback
        expected_tables = {}
        for f in feedback:
            tables = f.metadata.get("tables", [])
            if tables:
                expected_tables[f.question] = tables
        
        # Run GRPO step
        step = self.run_step(
            questions=questions,
            expected_tables=expected_tables,
            use_simulation=True
        )
        
        # Convert to visualization format
        viz_data = []
        for sample in step.samples:
            viz = GRPOVisualizationData.from_sample(sample)
            viz_data.append(viz)
        
        return viz_data
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get a summary of training progress."""
        return {
            "total_steps": self.state.total_steps,
            "total_samples": self.state.total_samples,
            "total_completions": self.state.total_completions,
            "avg_reward": round(self.state.avg_reward, 4),
            "best_completion_rate": f"{self.state.best_completion_rate * 100:.1f}%",
            "hints_created": self.state.total_hints_created,
            "hints_updated": self.state.total_hints_updated,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "last_updated": self.state.last_updated.isoformat(),
        }
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _build_sql_prompt(self, question: str, schema_context: str) -> str:
        """Build the SQL generation prompt."""
        return f"""Given this database schema:

{schema_context if schema_context else "No specific schema provided - use common table names."}

Generate a SQL query for: {question}

Rules:
- Use Presto SQL syntax
- Return ONLY the SQL query, no explanations
- Use proper formatting with newlines
"""
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response."""
        import re
        
        # Try to find SQL in code blocks
        code_block_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", response)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Remove common prefixes
        sql = response.strip()
        for prefix in ["SQL Query:", "Here is the SQL:", "Query:", "SQL:"]:
            if sql.upper().startswith(prefix.upper()):
                sql = sql[len(prefix):].strip()
        
        return sql
    
    def _create_sql_variation(self, base_sql: str, index: int) -> str:
        """Create a variation of SQL for simulation."""
        variations = [
            lambda s: s.replace("SELECT", "SELECT DISTINCT"),
            lambda s: s + " LIMIT 100" if "LIMIT" not in s.upper() else s,
            lambda s: s.replace("*", "column1, column2"),
            lambda s: s.replace("GROUP BY", "GROUP BY\n   "),
        ]
        
        if index < len(variations):
            return variations[index](base_sql)
        return base_sql
    
    def _create_synthetic_sql(self, question: str, index: int) -> str:
        """Create synthetic SQL for demo purposes."""
        templates = [
            "SELECT * FROM products WHERE category = 'electronics'",
            "SELECT p.name, SUM(o.amount) FROM products p JOIN orders o ON p.id = o.product_id GROUP BY p.name",
            "SELECT COUNT(*) FROM orders WHERE status = 'completed'",
            "SELECT customer_name FROM customers LIMIT 10",
        ]
        return templates[index % len(templates)]
    
    def _try_execute(self, sql: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Attempt to execute SQL (returns result or error)."""
        try:
            from app.services.athena import get_athena_service
            athena = get_athena_service()
            result, _ = athena.execute_query(sql, max_rows=1)
            return {"total_rows": result.total_rows, "columns": result.columns}, None
        except Exception as e:
            return None, str(e)
    
    def _log_sample_details(self, sample: GRPOSample):
        """Log details of a sample for verbose mode."""
        logger.info(f"\nQuestion: {sample.prompt}")
        logger.info(f"Group Statistics: mean={sample.mean_reward:.3f}, std={sample.std_reward:.3f}")
        logger.info(f"\nCompletions and Advantages:")
        
        for i, c in enumerate(sample.completions):
            status = "✅ REINFORCE" if c.advantage > 0 else "❌ PENALIZE"
            logger.info(f"  [{i+1}] Reward: {c.total_reward:+.3f}, Advantage: {c.advantage:+.3f} {status}")
            logger.info(f"      SQL: {c.sql[:80]}...")


# Singleton instance
_grpo_trainer: Optional[GRPOTrainer] = None


def get_grpo_trainer(config: Optional[GRPOConfig] = None) -> GRPOTrainer:
    """Get singleton GRPO trainer instance."""
    global _grpo_trainer
    if _grpo_trainer is None or config is not None:
        _grpo_trainer = GRPOTrainer(config)
    return _grpo_trainer
