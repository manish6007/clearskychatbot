"""S3 Client Service - Upload results and generate presigned URLs."""

import io
import csv
import json
import logging
from typing import Optional, List, Any
from datetime import datetime
import uuid

import boto3
from botocore.exceptions import ClientError

from app.services.s3_config_loader import get_chatbot_config
from app.models.chat import ResultPreview

logger = logging.getLogger(__name__)


class S3ClientService:
    """Service for S3 operations related to query results."""
    
    def __init__(self):
        self._client = None
    
    @property
    def config(self):
        """Get current S3 configuration."""
        return get_chatbot_config().s3
    
    @property
    def region(self):
        """Get AWS region."""
        return get_chatbot_config().bedrock.region
    
    @property
    def client(self):
        """Lazy initialization of S3 client."""
        if self._client is None:
            self._client = boto3.client("s3", region_name=self.region)
        return self._client
    
    def upload_result_csv(
        self,
        result: ResultPreview,
        session_id: str,
        message_id: str
    ) -> str:
        """
        Upload query result as CSV to S3.
        
        Returns:
            S3 key where the file was uploaded
        """
        # Generate file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"{session_id}_{message_id}_{timestamp}.csv"
        s3_key = f"{self.config.results_prefix}{file_name}"
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(result.columns)
        writer.writerows(result.rows)
        csv_content = output.getvalue()
        
        # Upload to S3
        try:
            self.client.put_object(
                Bucket=self.config.results_bucket,
                Key=s3_key,
                Body=csv_content.encode("utf-8"),
                ContentType="text/csv"
            )
            logger.info(f"Uploaded result to s3://{self.config.results_bucket}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload result: {e}")
            raise
    
    def upload_result_json(
        self,
        result: ResultPreview,
        session_id: str,
        message_id: str
    ) -> str:
        """
        Upload query result as JSON to S3.
        
        Returns:
            S3 key where the file was uploaded
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_name = f"{session_id}_{message_id}_{timestamp}.json"
        s3_key = f"{self.config.results_prefix}{file_name}"
        
        # Create JSON content
        json_content = {
            "columns": result.columns,
            "rows": result.rows,
            "total_rows": result.total_rows,
            "truncated": result.truncated,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        try:
            self.client.put_object(
                Bucket=self.config.results_bucket,
                Key=s3_key,
                Body=json.dumps(json_content, default=str).encode("utf-8"),
                ContentType="application/json"
            )
            logger.info(f"Uploaded result to s3://{self.config.results_bucket}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload result: {e}")
            raise
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiry_seconds: Optional[int] = None
    ) -> str:
        """
        Generate a presigned URL for downloading a result file.
        
        Returns:
            Presigned URL string
        """
        expiry = expiry_seconds or self.config.presigned_url_expiry
        
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.config.results_bucket,
                    "Key": s3_key
                },
                ExpiresIn=expiry
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def upload_and_get_url(
        self,
        result: ResultPreview,
        session_id: str,
        message_id: str,
        format: str = "csv"
    ) -> str:
        """
        Upload result and return presigned URL.
        
        Returns:
            Presigned URL for the uploaded file
        """
        if format == "json":
            s3_key = self.upload_result_json(result, session_id, message_id)
        else:
            s3_key = self.upload_result_csv(result, session_id, message_id)
        
        return self.generate_presigned_url(s3_key)
    
    def delete_result(self, s3_key: str) -> bool:
        """Delete a result file from S3."""
        try:
            self.client.delete_object(
                Bucket=self.config.results_bucket,
                Key=s3_key
            )
            logger.info(f"Deleted s3://{self.config.results_bucket}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete result: {e}")
            return False
    
    def list_session_results(self, session_id: str) -> List[dict]:
        """List all result files for a session."""
        prefix = f"{self.config.results_prefix}{session_id}_"
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.config.results_bucket,
                Prefix=prefix
            )
            
            results = []
            for obj in response.get("Contents", []):
                results.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat()
                })
            
            return results
            
        except ClientError as e:
            logger.error(f"Failed to list results: {e}")
            return []


# Singleton instance
_s3_client_service: Optional[S3ClientService] = None


def get_s3_client_service() -> S3ClientService:
    """Get singleton S3 client service instance."""
    global _s3_client_service
    if _s3_client_service is None:
        _s3_client_service = S3ClientService()
    return _s3_client_service
