"""GRPO Models - Data structures for GRPO training and analysis."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class GRPOCompletion(BaseModel):
    """A single completion within a GRPO group."""
    
    sql: str = Field(..., description="Generated SQL query")
    reward_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual reward component scores"
    )
    total_reward: float = Field(default=0.0, description="Combined reward score")
    advantage: float = Field(default=0.0, description="Group-relative advantage")
    execution_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result from SQL execution attempt"
    )
    execution_error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )


class GRPOSample(BaseModel):
    """A complete GRPO training sample with G completions."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = Field(..., description="User question/prompt")
    completions: List[GRPOCompletion] = Field(
        default_factory=list,
        description="List of G completions with their scores"
    )
    
    # Group statistics
    mean_reward: float = Field(default=0.0)
    std_reward: float = Field(default=0.0)
    best_completion_idx: int = Field(default=0)
    
    # Metadata
    tables_involved: List[str] = Field(default_factory=list)
    patterns_found: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def get_best_completion(self) -> GRPOCompletion:
        """Return the completion with highest reward."""
        if not self.completions:
            raise ValueError("No completions available")
        return self.completions[self.best_completion_idx]
    
    def get_positive_advantage_completions(self) -> List[GRPOCompletion]:
        """Return completions with positive advantage (above group average)."""
        return [c for c in self.completions if c.advantage > 0]


class GRPOStep(BaseModel):
    """A single GRPO training step with multiple samples."""
    
    step_number: int = Field(default=0)
    samples: List[GRPOSample] = Field(default_factory=list)
    
    # Step-level metrics
    avg_reward: float = Field(default=0.0)
    avg_positive_advantage: float = Field(default=0.0)
    avg_negative_advantage: float = Field(default=0.0)
    best_completion_rate: float = Field(default=0.0)
    
    # Policy updates made
    hints_created: int = Field(default=0)
    hints_updated: int = Field(default=0)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GRPOTrainingState(BaseModel):
    """Overall state of GRPO training."""
    
    # Training history
    total_steps: int = Field(default=0)
    total_samples: int = Field(default=0)
    total_completions: int = Field(default=0)
    
    # Aggregate metrics
    avg_reward: float = Field(default=0.0)
    avg_advantage_spread: float = Field(default=0.0)
    best_completion_rate: float = Field(default=0.0)
    
    # Recent history for visualization
    recent_steps: List[GRPOStep] = Field(
        default_factory=list,
        description="Last N training steps for visualization"
    )
    
    # Policy impact
    total_hints_created: int = Field(default=0)
    total_hints_updated: int = Field(default=0)
    
    # Timestamps
    started_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def add_step(self, step: GRPOStep, max_history: int = 10):
        """Add a training step and update aggregate metrics."""
        self.total_steps += 1
        self.total_samples += len(step.samples)
        self.total_completions += sum(
            len(s.completions) for s in step.samples
        )
        
        # Update running averages
        if self.avg_reward == 0:
            self.avg_reward = step.avg_reward
        else:
            self.avg_reward = 0.9 * self.avg_reward + 0.1 * step.avg_reward
        
        self.best_completion_rate = 0.9 * self.best_completion_rate + 0.1 * step.best_completion_rate
        
        # Update hints count
        self.total_hints_created += step.hints_created
        self.total_hints_updated += step.hints_updated
        
        # Keep recent history
        self.recent_steps.append(step)
        if len(self.recent_steps) > max_history:
            self.recent_steps = self.recent_steps[-max_history:]
        
        self.last_updated = datetime.utcnow()


class GRPOVisualizationData(BaseModel):
    """Data structure optimized for visualization/demo output."""
    
    question: str
    completions: List[Dict[str, Any]] = Field(default_factory=list)
    reward_stats: Dict[str, float] = Field(default_factory=dict)
    advantage_explanation: str = ""
    policy_impact: str = ""
    
    @classmethod
    def from_sample(cls, sample: GRPOSample) -> "GRPOVisualizationData":
        """Create visualization data from a GRPO sample."""
        completions = []
        for i, c in enumerate(sample.completions):
            completions.append({
                "index": i + 1,
                "sql": c.sql[:200] + "..." if len(c.sql) > 200 else c.sql,
                "rewards": c.reward_breakdown,
                "total_reward": round(c.total_reward, 3),
                "advantage": round(c.advantage, 3),
                "is_best": i == sample.best_completion_idx,
                "executed": c.execution_result is not None,
                "error": c.execution_error,
            })
        
        advantage_explanations = []
        for c in completions:
            if c["advantage"] > 0:
                advantage_explanations.append(
                    f"Completion {c['index']}: +{c['advantage']:.2f} (above average, REINFORCE)"
                )
            else:
                advantage_explanations.append(
                    f"Completion {c['index']}: {c['advantage']:.2f} (below average, penalize)"
                )
        
        return cls(
            question=sample.prompt,
            completions=completions,
            reward_stats={
                "mean": round(sample.mean_reward, 3),
                "std": round(sample.std_reward, 3),
                "best_reward": round(sample.completions[sample.best_completion_idx].total_reward, 3),
            },
            advantage_explanation="\n".join(advantage_explanations),
            policy_impact=f"Tables: {', '.join(sample.tables_involved)}\nPatterns: {', '.join(sample.patterns_found)}"
        )
