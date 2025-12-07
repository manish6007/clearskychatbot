"""AWS Athena Service - Execute SQL queries via Athena."""

import time
import logging
from typing import Optional, List, Any, Tuple
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from app.services.s3_config_loader import get_chatbot_config
from app.models.chat import ResultPreview

logger = logging.getLogger(__name__)


class AthenaQueryError(Exception):
    """Custom exception for Athena query errors."""
    def __init__(self, message: str, query_execution_id: Optional[str] = None):
        super().__init__(message)
        self.query_execution_id = query_execution_id


class AthenaService:
    """Service for executing queries via AWS Athena."""
    
    def __init__(self):
        self._client = None
    
    @property
    def config(self):
        """Get current Athena configuration."""
        return get_chatbot_config().athena
    
    @property
    def client(self):
        """Lazy initialization of Athena client."""
        if self._client is None:
            region = get_chatbot_config().bedrock.region
            self._client = boto3.client("athena", region_name=region)
        return self._client
    
    def execute_query(
        self,
        sql: str,
        database: Optional[str] = None,
        catalog: Optional[str] = None,
        max_rows: Optional[int] = None
    ) -> Tuple[ResultPreview, str]:
        """
        Execute a SQL query in Athena.
        
        Returns:
            Tuple of (ResultPreview, query_execution_id)
        """
        database = database or self.config.database
        catalog = catalog or self.config.catalog
        
        logger.info(f"Executing Athena query in {catalog}.{database}")
        logger.debug(f"SQL: {sql[:200]}...")
        
        try:
            # Start query execution
            response = self.client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={
                    "Database": database,
                    "Catalog": catalog
                },
                ResultConfiguration={
                    "OutputLocation": self.config.output_location_s3
                },
                WorkGroup=self.config.workgroup
            )
            
            query_execution_id = response["QueryExecutionId"]
            logger.info(f"Query started: {query_execution_id}")
            
            # Wait for completion
            self._wait_for_query(query_execution_id)
            
            # Fetch results
            result_preview = self._fetch_results(query_execution_id, max_rows)
            
            return result_preview, query_execution_id
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Athena error: {error_code} - {e}")
            raise AthenaQueryError(str(e))
    
    def _wait_for_query(self, query_execution_id: str) -> None:
        """Wait for query to complete or fail."""
        timeout = self.config.query_timeout_seconds
        start_time = time.time()
        poll_interval = 0.5
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                self.client.stop_query_execution(QueryExecutionId=query_execution_id)
                raise AthenaQueryError(
                    f"Query timed out after {timeout} seconds",
                    query_execution_id
                )
            
            response = self.client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            
            state = response["QueryExecution"]["Status"]["State"]
            
            if state == "SUCCEEDED":
                logger.info(f"Query completed: {query_execution_id}")
                return
            elif state == "FAILED":
                reason = response["QueryExecution"]["Status"].get(
                    "StateChangeReason", "Unknown error"
                )
                raise AthenaQueryError(reason, query_execution_id)
            elif state == "CANCELLED":
                raise AthenaQueryError("Query was cancelled", query_execution_id)
            
            # Still running, wait and poll again
            time.sleep(poll_interval)
            # Increase poll interval up to 2 seconds
            poll_interval = min(poll_interval * 1.5, 2.0)
    
    def _fetch_results(
        self,
        query_execution_id: str,
        max_rows: Optional[int] = None
    ) -> ResultPreview:
        """Fetch query results."""
        max_rows = max_rows or get_chatbot_config().features.default_max_rows
        
        columns: List[str] = []
        rows: List[List[Any]] = []
        total_rows = 0
        
        paginator = self.client.get_paginator("get_query_results")
        
        for page in paginator.paginate(
            QueryExecutionId=query_execution_id,
            PaginationConfig={"MaxItems": max_rows + 1}  # +1 for header
        ):
            result_set = page["ResultSet"]
            
            # Get column names from first page
            if not columns and "ResultSetMetadata" in result_set:
                columns = [
                    col["Name"] 
                    for col in result_set["ResultSetMetadata"]["ColumnInfo"]
                ]
            
            # Process rows
            for i, row in enumerate(result_set["Rows"]):
                # Skip header row
                if total_rows == 0 and i == 0:
                    continue
                
                row_data = [
                    cell.get("VarCharValue") 
                    for cell in row.get("Data", [])
                ]
                rows.append(row_data)
                total_rows += 1
                
                if len(rows) >= max_rows:
                    break
            
            if len(rows) >= max_rows:
                break
        
        return ResultPreview(
            columns=columns,
            rows=rows,
            total_rows=total_rows,
            truncated=total_rows > max_rows
        )
    
    def get_query_statistics(self, query_execution_id: str) -> dict:
        """Get execution statistics for a completed query."""
        response = self.client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        
        stats = response["QueryExecution"].get("Statistics", {})
        return {
            "data_scanned_bytes": stats.get("DataScannedInBytes", 0),
            "execution_time_ms": stats.get("EngineExecutionTimeInMillis", 0),
            "query_queue_time_ms": stats.get("QueryQueueTimeInMillis", 0),
            "total_execution_time_ms": stats.get("TotalExecutionTimeInMillis", 0)
        }
    
    def cancel_query(self, query_execution_id: str) -> bool:
        """Cancel a running query."""
        try:
            self.client.stop_query_execution(QueryExecutionId=query_execution_id)
            logger.info(f"Query cancelled: {query_execution_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to cancel query: {e}")
            return False
    
    def list_databases(self, catalog: Optional[str] = None) -> List[str]:
        """List available databases."""
        catalog = catalog or self.config.catalog
        
        databases = []
        paginator = self.client.get_paginator("list_databases")
        
        for page in paginator.paginate(CatalogName=catalog):
            for db in page.get("DatabaseList", []):
                databases.append(db["Name"])
        
        return databases
    
    def list_tables(
        self,
        database: Optional[str] = None,
        catalog: Optional[str] = None
    ) -> List[str]:
        """List tables in a database."""
        database = database or self.config.database
        catalog = catalog or self.config.catalog
        
        tables = []
        paginator = self.client.get_paginator("list_table_metadata")
        
        for page in paginator.paginate(CatalogName=catalog, DatabaseName=database):
            for table in page.get("TableMetadataList", []):
                tables.append(table["Name"])
        
        return tables


# Singleton instance
_athena_service: Optional[AthenaService] = None


def get_athena_service() -> AthenaService:
    """Get singleton Athena service instance."""
    global _athena_service
    if _athena_service is None:
        _athena_service = AthenaService()
    return _athena_service
