"""
Build Local FAISS Vector Store

This script creates a FAISS vector store from the schema documentation.
Uses sentence-transformers for local embeddings (no AWS needed for this step).
"""

import os
import json
from pathlib import Path
from typing import List, Dict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Configuration
SCHEMA_DOCS_DIR = Path(__file__).parent / "schema_docs"
FAISS_INDEX_DIR = Path(__file__).parent / "faiss_index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality local model
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2


def load_schema_documents() -> List[Dict]:
    """Load all schema documentation files."""
    documents = []
    
    for md_file in SCHEMA_DOCS_DIR.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract table name from filename
        table_name = md_file.stem
        
        # Create document chunks
        # Split by sections for better retrieval
        sections = content.split("\n## ")
        
        for i, section in enumerate(sections):
            if i == 0:
                # First section includes the title
                chunk_content = section
            else:
                chunk_content = "## " + section
            
            if chunk_content.strip():
                documents.append({
                    "content": chunk_content,
                    "metadata": {
                        "source": str(md_file),
                        "table": table_name,
                        "section_index": i,
                        "type": "schema"
                    }
                })
    
    print(f"Loaded {len(documents)} document chunks from {len(list(SCHEMA_DOCS_DIR.glob('*.md')))} files")
    return documents


def create_embeddings(documents: List[Dict], model: SentenceTransformer) -> np.ndarray:
    """Generate embeddings for all documents."""
    texts = [doc["content"] for doc in documents]
    
    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    return embeddings.astype("float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Build FAISS index with inner product similarity."""
    # Normalize embeddings for cosine similarity via inner product
    faiss.normalize_L2(embeddings)
    
    # Create index
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)
    
    print(f"Built FAISS index with {index.ntotal} vectors")
    return index


def save_index(index: faiss.IndexFlatIP, documents: List[Dict]):
    """Save FAISS index and document metadata."""
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save FAISS index
    index_path = FAISS_INDEX_DIR / "index.faiss"
    faiss.write_index(index, str(index_path))
    print(f"Saved FAISS index to {index_path}")
    
    # Save document metadata
    metadata_path = FAISS_INDEX_DIR / "documents.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2)
    print(f"Saved document metadata to {metadata_path}")


def create_local_config():
    """Create local configuration file if it doesn't exist."""
    config_path = Path(__file__).parent / "local_config.json"
    
    # Only create if doesn't exist - don't overwrite user's config
    if config_path.exists():
        print(f"Local config already exists at {config_path} - skipping")
    else:
        config = {
            "bedrock": {
                "region": "us-east-1",
                "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "embedding_model_id": "amazon.titan-embed-text-v2:0",
                "max_tokens": 4096,
                "temperature": 0.1
            },
            "athena": {
                "workgroup": "primary",
                "database": "athena_db",
                "catalog": "AwsDataCatalog",
                "output_location_s3": "s3://athena-datasource-cg/query-results/",
                "query_timeout_seconds": 300
            },
            "s3": {
                "results_bucket": "athena-datasource-cg",
                "results_prefix": "text2sql-results/",
                "presigned_url_expiry": 3600
            },
            "features": {
                "enable_streaming": False,
                "enable_advanced_charts": True,
                "default_max_rows": 1000,
                "large_result_threshold": 10000,
                "enable_sql_explanation": True,
                "enable_debug_mode": True
            },
            "app_name": "ClearSky Text-to-SQL",
            "version": "1.0.0"
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"Created local config at {config_path}")
    
    # Create vector store config (always recreate - has paths)
    vs_config = {
        "type": "faiss",
        "index_path": str(FAISS_INDEX_DIR / "index.faiss"),
        "documents_path": str(FAISS_INDEX_DIR / "documents.json"),
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIM,
        "top_k": 10,
        "similarity_threshold": 0.3
    }
    
    vs_config_path = Path(__file__).parent / "vector_store_config.json"
    with open(vs_config_path, "w", encoding="utf-8") as f:
        json.dump(vs_config, f, indent=2)
    print(f"Created vector store config at {vs_config_path}")


def main():
    print("=" * 60)
    print("Building Local FAISS Vector Store")
    print("=" * 60)
    
    # Load documents
    documents = load_schema_documents()
    
    if not documents:
        print("No documents found in schema_docs/")
        return
    
    # Load embedding model
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Create embeddings
    embeddings = create_embeddings(documents, model)
    
    # Build FAISS index
    index = build_faiss_index(embeddings)
    
    # Save everything
    save_index(index, documents)
    
    # Create local config
    create_local_config()
    
    print("\n" + "=" * 60)
    print("Vector store built successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set environment variables:")
    print("   set USE_LOCAL_CONFIG=true")
    print(f"   set LOCAL_CONFIG_PATH={Path(__file__).parent / 'local_config.json'}")
    print(f"   set LOCAL_VS_CONFIG_PATH={Path(__file__).parent / 'vector_store_config.json'}")
    print("\n2. Start the backend:")
    print("   cd ../backend")
    print("   python -m uvicorn app.main:app --reload")
    print("\n3. Start the frontend:")
    print("   cd ../frontend")
    print("   npm run dev")


if __name__ == "__main__":
    main()
