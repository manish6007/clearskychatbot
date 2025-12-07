"""Configuration models for S3-based JSON configs."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class BedrockConfig(BaseModel):
    """AWS Bedrock LLM configuration."""
    region: str = Field(default="us-east-1", description="AWS region for Bedrock")
    model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        description="Bedrock model ID for text generation"
    )
    embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0",
        description="Bedrock model ID for embeddings"
    )
    max_tokens: int = Field(default=4096, description="Max tokens for generation")
    temperature: float = Field(default=0.1, description="Temperature for generation")


class AthenaConfig(BaseModel):
    """AWS Athena configuration."""
    workgroup: str = Field(default="primary", description="Athena workgroup")
    database: str = Field(..., description="Default database name")
    catalog: str = Field(default="AwsDataCatalog", description="Data catalog name")
    output_location_s3: str = Field(..., description="S3 location for query results")
    query_timeout_seconds: int = Field(default=300, description="Query timeout in seconds")


class S3Config(BaseModel):
    """S3 bucket configuration."""
    results_bucket: str = Field(..., description="Bucket for storing large results")
    results_prefix: str = Field(default="query-results/", description="Prefix for results")
    presigned_url_expiry: int = Field(default=3600, description="Presigned URL expiry in seconds")


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""
    enable_streaming: bool = Field(default=True, description="Enable streaming responses")
    enable_advanced_charts: bool = Field(default=True, description="Enable advanced chart types")
    default_max_rows: int = Field(default=1000, description="Default max rows to return")
    large_result_threshold: int = Field(default=10000, description="Threshold for S3 upload")
    enable_sql_explanation: bool = Field(default=True, description="Enable SQL explanation")
    enable_debug_mode: bool = Field(default=False, description="Enable debug information")


class ChatbotConfig(BaseModel):
    """Main chatbot configuration loaded from S3."""
    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)
    athena: AthenaConfig
    s3: S3Config
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    app_name: str = Field(default="ClearSky Text-to-SQL", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")


class VectorStoreConfig(BaseModel):
    """Vector store configuration for connecting to existing store."""
    type: Literal["pgvector", "opensearch", "pinecone", "chroma"] = Field(
        default="pgvector",
        description="Vector store type"
    )
    connection_string: Optional[str] = Field(
        default=None,
        description="Connection string for database-backed stores"
    )
    host: Optional[str] = Field(default=None, description="Host for network-based stores")
    port: Optional[int] = Field(default=None, description="Port for network-based stores")
    index_name: Optional[str] = Field(default=None, description="Index/collection name")
    table: str = Field(default="knowledge_embeddings", description="Table name for pgvector")
    embedding_dimension: int = Field(default=1024, description="Embedding vector dimension")
    top_k: int = Field(default=10, description="Default number of results to retrieve")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")


class FrontendConfig(BaseModel):
    """Configuration subset exposed to frontend."""
    app_name: str
    version: str
    enable_advanced_charts: bool
    enable_streaming: bool
    default_max_rows: int
    enable_sql_explanation: bool
    enable_debug_mode: bool

    @classmethod
    def from_chatbot_config(cls, config: ChatbotConfig) -> "FrontendConfig":
        """Create frontend config from full chatbot config."""
        return cls(
            app_name=config.app_name,
            version=config.version,
            enable_advanced_charts=config.features.enable_advanced_charts,
            enable_streaming=config.features.enable_streaming,
            default_max_rows=config.features.default_max_rows,
            enable_sql_explanation=config.features.enable_sql_explanation,
            enable_debug_mode=config.features.enable_debug_mode,
        )
