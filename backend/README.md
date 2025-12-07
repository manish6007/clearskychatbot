# ClearSky Text-to-SQL Backend

Enterprise natural language to SQL query interface powered by AWS Bedrock (Claude Sonnet) and AWS Athena.

## Features

- **Natural Language Queries**: Ask questions in plain English, get SQL and results
- **AWS Bedrock Integration**: Uses Claude Sonnet 3.7 for SQL generation
- **AWS Athena Execution**: Direct query execution against your data lake
- **Vector Store Retrieval**: Semantic search for relevant schema context
- **Chart Recommendations**: Automatic visualization suggestions with Quick Chart
- **S3 Configuration**: All configuration loaded from S3 JSON files

## Prerequisites

- Python 3.11+
- AWS Account with:
  - Bedrock access (Claude Sonnet enabled)
  - Athena configured with data catalog
  - S3 buckets for config and results
  - (Optional) PostgreSQL with pgvector for vector store

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required: S3 Configuration
CONFIG_BUCKET=your-config-bucket
CHATBOT_CONFIG_KEY=configs/chatbot_config.json
VECTORSTORE_CONFIG_KEY=configs/vector_store_config.json
AWS_REGION=us-east-1

# Optional
LOG_LEVEL=INFO
JSON_LOGS=false
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
HOST=0.0.0.0
PORT=8000
```

### Chatbot Config JSON (S3)

Create `configs/chatbot_config.json` in your config bucket:

```json
{
  "bedrock": {
    "region": "us-east-1",
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "embedding_model_id": "amazon.titan-embed-text-v2:0",
    "max_tokens": 4096,
    "temperature": 0.1
  },
  "athena": {
    "workgroup": "primary",
    "database": "your_database",
    "catalog": "AwsDataCatalog",
    "output_location_s3": "s3://your-athena-output-bucket/results/",
    "query_timeout_seconds": 300
  },
  "s3": {
    "results_bucket": "your-results-bucket",
    "results_prefix": "query-results/",
    "presigned_url_expiry": 3600
  },
  "features": {
    "enable_streaming": true,
    "enable_advanced_charts": true,
    "default_max_rows": 1000,
    "large_result_threshold": 10000,
    "enable_sql_explanation": true,
    "enable_debug_mode": false
  },
  "app_name": "ClearSky Text-to-SQL",
  "version": "1.0.0"
}
```

### Vector Store Config JSON (S3)

Create `configs/vector_store_config.json` in your config bucket:

```json
{
  "type": "pgvector",
  "connection_string": "postgresql+psycopg://user:password@host:5432/database",
  "table": "knowledge_embeddings",
  "embedding_dimension": 1024,
  "top_k": 10,
  "similarity_threshold": 0.7
}
```

**Note**: The vector store must already exist and be populated with your schema documentation. This application does NOT create or populate the vector store.

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running Locally

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m app.main
```

API will be available at `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Chat
- `POST /api/chat/query` - Submit a natural language question
- `GET /api/chat/updates` - Poll for query status
- `GET /api/chat/history` - Get chat history
- `GET /api/chat/session/{id}` - Get session details

### Schema
- `GET /api/schema/tables` - List tables
- `GET /api/schema/table/{name}` - Get table details
- `GET /api/schema/databases` - List databases
- `GET /api/schema/search` - Semantic schema search

### Config
- `GET /api/config` - Get frontend configuration
- `POST /api/config/reload` - Reload config from S3
- `GET /api/config/health` - Health check

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/                  # API endpoints
│   │   ├── chat.py
│   │   ├── schema.py
│   │   ├── history.py
│   │   └── config.py
│   ├── agents/               # LlamaIndex agents
│   │   └── text_to_sql_agent.py
│   ├── services/             # AWS service clients
│   │   ├── s3_config_loader.py
│   │   ├── bedrock_llm.py
│   │   ├── athena.py
│   │   ├── s3_client.py
│   │   └── vector_store_client.py
│   ├── knowledge/            # Schema resolution
│   │   └── schema_resolver.py
│   ├── models/               # Pydantic models
│   │   ├── config_models.py
│   │   ├── chat.py
│   │   ├── schema.py
│   │   └── visualization.py
│   └── utils/                # Utilities
│       ├── sql_utils.py
│       ├── result_utils.py
│       └── logging_utils.py
├── requirements.txt
└── README.md
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ECS Task Definition

Configure the following environment variables in your ECS task:
- `CONFIG_BUCKET`
- `CHATBOT_CONFIG_KEY`
- `VECTORSTORE_CONFIG_KEY`
- `AWS_REGION`

Ensure the task role has permissions for:
- S3: GetObject on config bucket
- S3: PutObject, GetObject on results bucket
- Bedrock: InvokeModel
- Athena: StartQueryExecution, GetQueryExecution, GetQueryResults

## License

MIT License
