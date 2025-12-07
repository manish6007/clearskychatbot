"""Vector Store Client - Connect to existing vector store for retrieval."""

import os
import json
import logging
from typing import Optional, List
from abc import ABC, abstractmethod
from pathlib import Path

from app.services.s3_config_loader import get_vector_store_config
from app.models.schema import RetrievedChunk

logger = logging.getLogger(__name__)


class VectorStoreClient(ABC):
    """Abstract base class for vector store clients."""
    
    @abstractmethod
    def search_similar(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the vector store is accessible."""
        pass


class FAISSClient(VectorStoreClient):
    """FAISS-based vector store client for local development."""
    
    def __init__(self):
        self._index = None
        self._documents = None
        self._model = None
        self._config = None
    
    @property
    def config(self):
        """Get vector store configuration."""
        if self._config is None:
            self._config = get_vector_store_config()
        return self._config
    
    def _load_index(self):
        """Load FAISS index and documents."""
        if self._index is not None:
            return
        
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            
            # Load index
            index_path = self.config.index_path if hasattr(self.config, 'index_path') else None
            if not index_path:
                # Try default local path
                local_setup_dir = Path(__file__).parent.parent.parent / "local_setup"
                index_path = str(local_setup_dir / "faiss_index" / "index.faiss")
            
            logger.info(f"Loading FAISS index from {index_path}")
            self._index = faiss.read_index(index_path)
            
            # Load documents
            docs_path = self.config.documents_path if hasattr(self.config, 'documents_path') else None
            if not docs_path:
                local_setup_dir = Path(__file__).parent.parent.parent / "local_setup"
                docs_path = str(local_setup_dir / "faiss_index" / "documents.json")
            
            with open(docs_path, "r", encoding="utf-8") as f:
                self._documents = json.load(f)
            
            # Load embedding model
            model_name = getattr(self.config, 'embedding_model', 'all-MiniLM-L6-v2')
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            
            logger.info(f"FAISS index loaded with {self._index.ntotal} vectors")
            
        except ImportError as e:
            logger.error(f"FAISS dependencies not installed: {e}")
            logger.error("Install with: pip install faiss-cpu sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise
    
    def search_similar(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """Search for similar documents using FAISS."""
        self._load_index()
        
        top_k = top_k or self.config.top_k
        
        try:
            import faiss
            import numpy as np
            
            # Generate query embedding
            query_embedding = self._model.encode([query], convert_to_numpy=True)
            query_embedding = query_embedding.astype("float32")
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self._index.search(query_embedding, top_k)
            
            results = []
            threshold = getattr(self.config, 'similarity_threshold', 0.3)
            
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or score < threshold:
                    continue
                
                doc = self._documents[idx]
                results.append(RetrievedChunk(
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    score=float(score),
                    source=doc.get("metadata", {}).get("source")
                ))
            
            logger.info(f"Found {len(results)} relevant chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if FAISS is accessible."""
        try:
            self._load_index()
            return self._index is not None
        except Exception as e:
            logger.error(f"FAISS health check failed: {e}")
            return False


class PgVectorClient(VectorStoreClient):
    """PostgreSQL pgvector client for semantic search."""
    
    def __init__(self):
        self._connection = None
        self._config = get_vector_store_config()
    
    @property
    def config(self):
        """Get current vector store configuration."""
        return get_vector_store_config()
    
    def _get_connection(self):
        """Get database connection."""
        if self._connection is None or self._connection.closed:
            try:
                import psycopg
                self._connection = psycopg.connect(self.config.connection_string)
            except ImportError:
                logger.error("psycopg not installed. Install with: pip install psycopg[binary]")
                raise
        return self._connection
    
    def search_similar(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """Search for similar documents using pgvector."""
        top_k = top_k or self.config.top_k
        
        # Get embedding for query - need Bedrock for this
        from app.services.bedrock_llm import get_bedrock_service
        bedrock_service = get_bedrock_service()
        query_embedding = bedrock_service.get_embeddings(query)
        
        if not query_embedding:
            logger.warning("Failed to get query embedding")
            return []
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                sql = f"""
                    SELECT 
                        content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM {self.config.table}
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                
                embedding_str = f"[{','.join(map(str, query_embedding))}]"
                cur.execute(sql, (
                    embedding_str,
                    embedding_str,
                    self.config.similarity_threshold,
                    embedding_str,
                    top_k
                ))
                
                results = []
                for row in cur.fetchall():
                    content, metadata, similarity = row
                    results.append(RetrievedChunk(
                        content=content,
                        metadata=metadata or {},
                        score=float(similarity),
                        source=metadata.get("source") if metadata else None
                    ))
                
                return results
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if pgvector is accessible."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None


class MockVectorClient(VectorStoreClient):
    """Mock vector client for testing when no real store is available."""
    
    def search_similar(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """Return mock results for testing."""
        logger.warning("Using mock vector client - no real vector store configured")
        
        return [
            RetrievedChunk(
                content="""
                # Schema Overview
                
                E-commerce database with customer orders and product catalog.
                
                ## Tables
                - customers: customerid, firstname, lastname, email, phonenumber
                - orders: orderid, customerid, orderdate, orderamount, orderstatus
                - order_items: orderitemid, orderid, productid, quantity, unitprice
                - products: productid, productname, category, price, stockquantity
                
                ## Relationships
                customers (1) ─ (N) orders (1) ─ (N) order_items (N) ─ (1) products
                """,
                metadata={"type": "schema", "table": "all"},
                score=0.9,
                source="schema_overview.md"
            )
        ]
    
    def health_check(self) -> bool:
        """Mock client is always healthy."""
        return True


def create_vector_client() -> VectorStoreClient:
    """Factory function to create appropriate vector client."""
    config = get_vector_store_config()
    
    # Check for local FAISS first
    if config.type == "faiss" or os.environ.get("USE_LOCAL_CONFIG") == "true":
        try:
            client = FAISSClient()
            if client.health_check():
                logger.info("Using FAISS vector store")
                return client
        except Exception as e:
            logger.warning(f"Failed to create FAISS client: {e}")
    
    # Try pgvector
    if config.type == "pgvector" and config.connection_string:
        try:
            client = PgVectorClient()
            if client.health_check():
                logger.info("Using pgvector store")
                return client
        except Exception as e:
            logger.warning(f"Failed to create pgvector client: {e}")
    
    # Fall back to mock
    logger.info("Using mock vector client")
    return MockVectorClient()


# Singleton instance
_vector_client: Optional[VectorStoreClient] = None


def get_vector_client() -> VectorStoreClient:
    """Get singleton vector client instance."""
    global _vector_client
    if _vector_client is None:
        _vector_client = create_vector_client()
    return _vector_client
