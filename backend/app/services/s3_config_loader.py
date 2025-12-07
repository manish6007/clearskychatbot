"""S3 Configuration Loader - Loads chatbot and vector store configs from S3 or local files."""

import os
import json
import logging
from typing import Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.models.config_models import ChatbotConfig, VectorStoreConfig

logger = logging.getLogger(__name__)


class LocalVectorStoreConfig:
    """Vector store config that supports FAISS-specific fields."""
    def __init__(self, data: dict):
        self.type = data.get("type", "faiss")
        self.index_path = data.get("index_path")
        self.documents_path = data.get("documents_path")
        self.embedding_model = data.get("embedding_model", "all-MiniLM-L6-v2")
        self.embedding_dimension = data.get("embedding_dimension", 384)
        self.top_k = data.get("top_k", 10)
        self.similarity_threshold = data.get("similarity_threshold", 0.3)
        self.connection_string = data.get("connection_string")
        self.table = data.get("table", "knowledge_embeddings")


class S3ConfigLoader:
    """Loads and caches configuration from S3 JSON files or local files."""
    
    _instance: Optional["S3ConfigLoader"] = None
    _chatbot_config: Optional[ChatbotConfig] = None
    _vector_store_config = None  # Can be VectorStoreConfig or LocalVectorStoreConfig
    
    def __init__(self):
        self.use_local = os.environ.get("USE_LOCAL_CONFIG", "false").lower() == "true"
        self.local_config_path = os.environ.get("LOCAL_CONFIG_PATH")
        self.local_vs_config_path = os.environ.get("LOCAL_VS_CONFIG_PATH")
        
        self.config_bucket = os.environ.get("CONFIG_BUCKET")
        self.chatbot_config_key = os.environ.get("CHATBOT_CONFIG_KEY", "configs/chatbot_config.json")
        self.vectorstore_config_key = os.environ.get("VECTORSTORE_CONFIG_KEY", "configs/vector_store_config.json")
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        
        if self.use_local:
            logger.info("Using local configuration files")
        elif not self.config_bucket:
            logger.warning("CONFIG_BUCKET not set and USE_LOCAL_CONFIG not true. Will use defaults.")
        
        self._s3_client = None
    
    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self.region)
        return self._s3_client
    
    def _load_json_from_file(self, path: str) -> dict:
        """Load a JSON file from local filesystem."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_json_from_s3(self, key: str) -> dict:
        """Load a JSON file from S3."""
        if not self.config_bucket:
            raise ValueError("CONFIG_BUCKET environment variable is required")
        
        try:
            response = self.s3_client.get_object(Bucket=self.config_bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Failed to load config from s3://{self.config_bucket}/{key}: {error_code}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in s3://{self.config_bucket}/{key}: {e}")
            raise
    
    def _get_default_local_paths(self):
        """Get default paths for local config files."""
        # Look for local_setup directory relative to this file
        backend_dir = Path(__file__).parent.parent.parent
        local_setup_dir = backend_dir.parent / "local_setup"
        
        return {
            "chatbot": local_setup_dir / "local_config.json",
            "vector_store": local_setup_dir / "vector_store_config.json"
        }
    
    def load_chatbot_config(self, force_reload: bool = False) -> ChatbotConfig:
        """Load chatbot configuration from S3 or local file."""
        if self._chatbot_config is not None and not force_reload:
            return self._chatbot_config
        
        # Try local file first if USE_LOCAL_CONFIG is set
        if self.use_local:
            config_path = self.local_config_path
            if not config_path:
                config_path = str(self._get_default_local_paths()["chatbot"])
            
            if Path(config_path).exists():
                logger.info(f"Loading chatbot config from local file: {config_path}")
                config_data = self._load_json_from_file(config_path)
                self._chatbot_config = ChatbotConfig(**config_data)
                return self._chatbot_config
        
        # Try S3 if bucket is configured
        if self.config_bucket:
            try:
                logger.info(f"Loading chatbot config from s3://{self.config_bucket}/{self.chatbot_config_key}")
                config_data = self._load_json_from_s3(self.chatbot_config_key)
                self._chatbot_config = ChatbotConfig(**config_data)
                logger.info("Chatbot config loaded successfully")
                return self._chatbot_config
            except Exception as e:
                logger.warning(f"Failed to load from S3: {e}")
        
        # Fall back to default
        logger.warning("Using default chatbot config")
        self._chatbot_config = ChatbotConfig(
            athena={
                "database": "default",
                "output_location_s3": "s3://athena-datasource-cg/query-results/"
            },
            s3={
                "results_bucket": "athena-datasource-cg"
            }
        )
        return self._chatbot_config
    
    def load_vector_store_config(self, force_reload: bool = False):
        """Load vector store configuration from S3 or local file."""
        if self._vector_store_config is not None and not force_reload:
            return self._vector_store_config
        
        # Try local file first if USE_LOCAL_CONFIG is set
        if self.use_local:
            config_path = self.local_vs_config_path
            if not config_path:
                config_path = str(self._get_default_local_paths()["vector_store"])
            
            if Path(config_path).exists():
                logger.info(f"Loading vector store config from local file: {config_path}")
                config_data = self._load_json_from_file(config_path)
                self._vector_store_config = LocalVectorStoreConfig(config_data)
                return self._vector_store_config
        
        # Try S3 if bucket is configured
        if self.config_bucket:
            try:
                logger.info(f"Loading vector store config from s3://{self.config_bucket}/{self.vectorstore_config_key}")
                config_data = self._load_json_from_s3(self.vectorstore_config_key)
                self._vector_store_config = VectorStoreConfig(**config_data)
                logger.info("Vector store config loaded successfully")
                return self._vector_store_config
            except Exception as e:
                logger.warning(f"Failed to load from S3: {e}")
        
        # Fall back to default FAISS config
        logger.warning("Using default FAISS vector store config")
        default_paths = self._get_default_local_paths()
        self._vector_store_config = LocalVectorStoreConfig({
            "type": "faiss",
            "index_path": str(default_paths["vector_store"].parent / "faiss_index" / "index.faiss"),
            "documents_path": str(default_paths["vector_store"].parent / "faiss_index" / "documents.json"),
            "embedding_model": "all-MiniLM-L6-v2",
            "top_k": 10
        })
        return self._vector_store_config
    
    def reload_configs(self) -> None:
        """Reload all configurations."""
        logger.info("Reloading all configurations...")
        self.load_chatbot_config(force_reload=True)
        self.load_vector_store_config(force_reload=True)
        logger.info("All configurations reloaded")
    
    @classmethod
    def get_instance(cls) -> "S3ConfigLoader":
        """Get singleton instance of the config loader."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_config_loader() -> S3ConfigLoader:
    """Get the global config loader instance."""
    return S3ConfigLoader.get_instance()


def get_chatbot_config() -> ChatbotConfig:
    """Convenience function to get chatbot config."""
    return get_config_loader().load_chatbot_config()


def get_vector_store_config():
    """Convenience function to get vector store config."""
    return get_config_loader().load_vector_store_config()


def reload_configs() -> None:
    """Convenience function to reload all configs."""
    get_config_loader().reload_configs()
