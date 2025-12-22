"""GRPO Configuration - Hyperparameters and settings for GRPO training."""

from pydantic import BaseModel, Field
from typing import List, Optional


class GRPOConfig(BaseModel):
    """Configuration for GRPO training simulation.
    
    GRPO Key Parameters Explained:
    - group_size (G): Number of responses to generate per question
    - temperature_sampling: Temperature for diverse response generation
    - kl_coef: Coefficient for KL divergence regularization (prevents model drift)
    - scale_rewards: Whether to normalize rewards by std (can cause difficulty bias if True)
    """
    
    # Group sampling parameters
    group_size: int = Field(
        default=4, 
        ge=2, 
        le=16,
        description="Number of completions to generate per prompt (G in GRPO)"
    )
    
    temperature_sampling: float = Field(
        default=0.7,
        ge=0.1,
        le=2.0,
        description="Temperature for generating diverse responses"
    )
    
    # Reward function weights
    reward_weights: dict = Field(
        default={
            "sql_validity": 0.20,
            "execution_success": 0.30,
            "result_quality": 0.35,
            "format_quality": 0.15,
        },
        description="Weights for different reward components"
    )
    
    # GRPO algorithm parameters
    kl_coef: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="KL divergence regularization coefficient"
    )
    
    scale_rewards: bool = Field(
        default=True,
        description="Whether to scale rewards by std (group normalization)"
    )
    
    clip_advantage: float = Field(
        default=4.0,
        ge=1.0,
        description="Maximum absolute advantage value (clipping for stability)"
    )
    
    # Training parameters
    learning_rate: float = Field(
        default=0.1,
        ge=0.01,
        le=1.0,
        description="Weight update rate for policy hints"
    )
    
    min_advantage_threshold: float = Field(
        default=0.3,
        description="Minimum advantage to trigger policy update"
    )
    
    # Storage
    storage_path: Optional[str] = Field(
        default=None,
        description="Path for GRPO state storage (uses rlhf_data if None)"
    )
    
    # Demo/visualization settings
    verbose: bool = Field(
        default=True,
        description="Enable verbose output for demonstrations"
    )
    
    save_intermediate_results: bool = Field(
        default=True,
        description="Save intermediate results for analysis"
    )


# Default configuration instance
DEFAULT_GRPO_CONFIG = GRPOConfig()
