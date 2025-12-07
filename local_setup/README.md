# Local Setup for ClearSky Text-to-SQL

This folder contains scripts to set up a local FAISS vector store for testing.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build the vector store:
```bash
python build_vector_store.py
```

3. Start the backend (from the backend folder):
```bash
cd ../backend
python -m app.main
```

4. Start the frontend (from the frontend folder):
```bash
cd ../frontend
npm install
npm run dev
```

## What This Does

- Creates schema documentation from your Athena table definitions
- Generates embeddings using a local sentence-transformers model (no AWS needed for embeddings)
- Stores everything in a local FAISS index
- Configures the backend to use local files instead of S3

## Files

- `schema_docs/` - Generated markdown documentation for each table
- `faiss_index/` - The FAISS vector store
- `local_config.json` - Local configuration (no S3 required)
- `build_vector_store.py` - Script to build the vector store
