"""Schema API Endpoints - Database schema exploration."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.models.schema import TableInfo, ColumnInfo, SchemaInfo
from app.services.athena import get_athena_service
from app.services.s3_config_loader import get_chatbot_config
from app.knowledge.schema_resolver import get_schema_resolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schema", tags=["schema"])


@router.get("/tables", response_model=List[TableInfo])
async def list_tables(
    database: Optional[str] = None,
    catalog: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List available tables.
    
    If search is provided, filters using vector store for semantic search.
    """
    config = get_chatbot_config()
    athena = get_athena_service()
    
    database = database or config.athena.database
    catalog = catalog or config.athena.catalog
    
    if search:
        # Use vector store for semantic search
        resolver = get_schema_resolver()
        context = resolver.resolve_schema_context(search)
        return context.relevant_tables
    
    # List from Athena metadata
    try:
        table_names = athena.list_tables(database=database, catalog=catalog)
        
        tables = []
        for name in table_names:
            tables.append(TableInfo(
                catalog=catalog,
                database=database,
                name=name,
                full_name=f"{database}.{name}",
                columns=[]
            ))
        
        return tables
        
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table/{table_name}", response_model=TableInfo)
async def get_table_details(
    table_name: str,
    database: Optional[str] = None,
    catalog: Optional[str] = None
):
    """
    Get detailed information about a specific table.
    """
    config = get_chatbot_config()
    
    database = database or config.athena.database
    catalog = catalog or config.athena.catalog
    
    # Try to get from vector store first
    resolver = get_schema_resolver()
    context = resolver.resolve_schema_context(f"table {table_name}")
    
    for table in context.relevant_tables:
        if table.name.lower() == table_name.lower():
            return table
    
    # Fall back to basic info
    return TableInfo(
        catalog=catalog,
        database=database,
        name=table_name,
        full_name=f"{database}.{table_name}",
        columns=[]
    )


@router.get("/databases", response_model=List[str])
async def list_databases(catalog: Optional[str] = None):
    """
    List available databases.
    """
    config = get_chatbot_config()
    athena = get_athena_service()
    
    catalog = catalog or config.athena.catalog
    
    try:
        databases = athena.list_databases(catalog=catalog)
        return databases
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[TableInfo])
async def search_schema(
    query: str = Query(..., min_length=2),
    top_k: int = Query(default=10, ge=1, le=50)
):
    """
    Semantic search across schema documentation.
    """
    resolver = get_schema_resolver()
    context = resolver.resolve_schema_context(query, top_k=top_k)
    
    return context.relevant_tables
