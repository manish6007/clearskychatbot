"""Schema Resolver - Resolves relevant schema context using vector store."""

import logging
import re
from typing import Optional, List

from app.services.vector_store_client import get_vector_client
from app.models.schema import SchemaContext, TableInfo, ColumnInfo, RetrievedChunk

logger = logging.getLogger(__name__)


class SchemaResolver:
    """Resolves schema information using vector store retrieval."""
    
    def __init__(self):
        self.vector_client = get_vector_client()
    
    def resolve_schema_context(
        self,
        question: str,
        top_k: Optional[int] = None
    ) -> SchemaContext:
        """
        Retrieve relevant schema context for a natural language question.
        
        Returns:
            SchemaContext with relevant tables, columns, and domain context
        """
        logger.info(f"Resolving schema context for: {question[:100]}...")
        
        # Search vector store for relevant chunks
        chunks = self.vector_client.search_similar(question, top_k)
        
        if not chunks:
            logger.warning("No relevant schema context found")
            return SchemaContext(
                relevant_tables=[],
                relevant_columns=[],
                domain_context="",
                retrieved_chunks=[]
            )
        
        # Parse chunks to extract structured schema info
        tables = self._extract_tables_from_chunks(chunks)
        columns = self._extract_columns_from_chunks(chunks)
        domain_context = self._build_domain_context(chunks)
        
        logger.info(f"Found {len(tables)} relevant tables and {len(columns)} columns")
        
        return SchemaContext(
            relevant_tables=tables,
            relevant_columns=columns,
            domain_context=domain_context,
            retrieved_chunks=chunks
        )
    
    def _extract_tables_from_chunks(
        self,
        chunks: List[RetrievedChunk]
    ) -> List[TableInfo]:
        """Extract table information from retrieved chunks."""
        tables = []
        seen_tables = set()
        
        for chunk in chunks:
            # Try to extract table name from metadata
            table_name = chunk.metadata.get("table")
            
            if not table_name:
                # Try to parse from content
                table_match = re.search(
                    r"Table:\s*(\w+)",
                    chunk.content,
                    re.IGNORECASE
                )
                if table_match:
                    table_name = table_match.group(1)
            
            if table_name and table_name not in seen_tables:
                seen_tables.add(table_name)
                
                # Extract columns for this table
                columns = self._parse_columns_from_content(chunk.content)
                
                tables.append(TableInfo(
                    catalog=chunk.metadata.get("catalog", "AwsDataCatalog"),
                    database=chunk.metadata.get("database", "default"),
                    name=table_name,
                    full_name=f"{chunk.metadata.get('database', 'default')}.{table_name}",
                    description=chunk.metadata.get("description"),
                    columns=columns
                ))
        
        return tables
    
    def _parse_columns_from_content(self, content: str) -> List[ColumnInfo]:
        """Parse column definitions from chunk content."""
        columns = []
        
        # Pattern to match column definitions like "- column_name (TYPE): description"
        column_pattern = re.compile(
            r"-\s+(\w+)\s+\(([^)]+)\)(?::\s*(.+))?",
            re.MULTILINE
        )
        
        for match in column_pattern.finditer(content):
            name = match.group(1)
            data_type = match.group(2)
            description = match.group(3).strip() if match.group(3) else None
            
            columns.append(ColumnInfo(
                name=name,
                data_type=data_type,
                description=description
            ))
        
        return columns
    
    def _extract_columns_from_chunks(
        self,
        chunks: List[RetrievedChunk]
    ) -> List[str]:
        """Extract column names from all chunks."""
        columns = set()
        
        for chunk in chunks:
            # Look for column references in content
            for col in self._parse_columns_from_content(chunk.content):
                columns.add(col.name)
        
        return list(columns)
    
    def _build_domain_context(self, chunks: List[RetrievedChunk]) -> str:
        """Build concatenated domain context from chunks."""
        context_parts = []
        
        for chunk in chunks:
            # Include chunk content with source annotation
            source = chunk.source or "unknown"
            context_parts.append(f"--- From {source} (relevance: {chunk.score:.2f}) ---\n{chunk.content}")
        
        return "\n\n".join(context_parts)
    
    def format_schema_for_prompt(self, context: SchemaContext) -> str:
        """Format schema context for inclusion in LLM prompt."""
        parts = []
        
        if context.relevant_tables:
            parts.append("## Available Tables and Columns\n")
            
            for table in context.relevant_tables:
                parts.append(f"### {table.full_name}")
                if table.description:
                    parts.append(f"Description: {table.description}")
                
                if table.columns:
                    parts.append("Columns:")
                    for col in table.columns:
                        col_desc = f"  - {col.name} ({col.data_type})"
                        if col.description:
                            col_desc += f": {col.description}"
                        parts.append(col_desc)
                parts.append("")
        
        if context.domain_context:
            parts.append("## Additional Context\n")
            parts.append(context.domain_context)
        
        return "\n".join(parts)


# Singleton instance
_schema_resolver: Optional[SchemaResolver] = None


def get_schema_resolver() -> SchemaResolver:
    """Get singleton schema resolver instance."""
    global _schema_resolver
    if _schema_resolver is None:
        _schema_resolver = SchemaResolver()
    return _schema_resolver
