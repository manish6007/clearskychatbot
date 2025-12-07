"""Schema models for database metadata."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Information about a database column."""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Column data type")
    description: Optional[str] = Field(default=None, description="Column description")
    is_nullable: bool = Field(default=True, description="Whether column allows NULL")
    is_partition_key: bool = Field(default=False, description="Whether column is partition key")
    sample_values: Optional[List[str]] = Field(default=None, description="Sample values")


class TableInfo(BaseModel):
    """Information about a database table."""
    catalog: str = Field(..., description="Data catalog name")
    database: str = Field(..., description="Database name")
    name: str = Field(..., description="Table name")
    full_name: str = Field(..., description="Fully qualified table name")
    description: Optional[str] = Field(default=None, description="Table description")
    columns: List[ColumnInfo] = Field(default_factory=list, description="Table columns")
    row_count: Optional[int] = Field(default=None, description="Approximate row count")
    size_bytes: Optional[int] = Field(default=None, description="Table size in bytes")
    partition_keys: List[str] = Field(default_factory=list, description="Partition key columns")
    location: Optional[str] = Field(default=None, description="S3 location for table data")


class SchemaInfo(BaseModel):
    """Information about a database schema/database."""
    catalog: str = Field(..., description="Data catalog name")
    name: str = Field(..., description="Database/schema name")
    description: Optional[str] = Field(default=None, description="Schema description")
    tables: List[TableInfo] = Field(default_factory=list, description="Tables in schema")


class RetrievedChunk(BaseModel):
    """A chunk retrieved from the vector store."""
    content: str = Field(..., description="Text content of the chunk")
    metadata: dict = Field(default_factory=dict, description="Chunk metadata")
    score: float = Field(..., description="Similarity score")
    source: Optional[str] = Field(default=None, description="Source document/file")


class SchemaContext(BaseModel):
    """Context retrieved for schema resolution."""
    relevant_tables: List[TableInfo] = Field(default_factory=list)
    relevant_columns: List[str] = Field(default_factory=list)
    domain_context: str = Field(default="", description="Domain knowledge context")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
