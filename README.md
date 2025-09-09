# Nazarriya LLM Service

  * [Features](#features)
  * [Architecture](#architecture)
    + [Security Flow](#security-flow)
  * [Prerequisites](#prerequisites)
  * [Environment Variables](#environment-variables)
  * [Installation](#installation)
    + [Local Development](#local-development)
    + [Docker Deployment](#docker-deployment)
  * [API Endpoints](#api-endpoints)
    + [Health Check](#health-check)
    + [Document Management](#document-management)
    + [Encrypted RAG Operations](#encrypted-rag-operations)
    + [Dataset Management](#dataset-management)
    + [Documentation](#documentation)
  * [Usage Examples](#usage-examples)
    + [Query the Encrypted RAG System](#query-the-encrypted-rag-system)
    + [Upload a Document](#upload-a-document)
    + [Ingest Documents from Paths](#ingest-documents-from-paths)
    + [Dataset Management](#dataset-management-1)
      - [Add Dataset Item](#add-dataset-item)
      - [Ingest Dataset File](#ingest-dataset-file)
      - [Test Dataset Query (Encrypted)](#test-dataset-query--encrypted-)
  * [Document Processing](#document-processing)
    + [Supported Formats](#supported-formats)
    + [Secure Processing Pipeline](#secure-processing-pipeline)
  * [Configuration](#configuration)
    + [Required Configuration](#required-configuration)
    + [Optional Configuration](#optional-configuration)
    + [Security Configuration](#security-configuration)
  * [Deployment](#deployment)
    + [Hetzner Deployment](#hetzner-deployment)
    + [Production Considerations](#production-considerations)
  * [Monitoring and Logging](#monitoring-and-logging)
  * [Troubleshooting](#troubleshooting)
    + [Common Issues](#common-issues)
    + [Logs](#logs)
  * [Development](#development)
    + [Project Structure](#project-structure)
    + [Adding New Features](#adding-new-features)
    + [Dataset Management](#dataset-management-2)
  * [License](#license)
  * [Support](#support)


A secure, RAG-powered LLM service using OpenAI and Langchain, designed to work with the Nazarriya application. This service provides end-to-end encrypted communication for maximum privacy and security.

## Features

- **End-to-End Encryption**: All queries and responses are encrypted using AES-GCM
- **Document Processing**: Support for PDF and HTML documents
- **Vector Storage**: ChromaDB-based vector database for efficient retrieval
- **RAG Pipeline**: Retrieval-Augmented Generation using OpenAI models
- **Secure API**: FastAPI-based service with encrypted endpoints
- **Containerized**: Docker support for easy deployment
- **Content Integrity**: SHA-256 hashing for message integrity verification

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main API      │───▶│   LLM Service    │───▶│   OpenAI API    │
│ (nazarriya-api) │    │ (nazarriya-llm) │    │                 │
│ [Encrypted]     │    │ [Decrypt/Encrypt]│    │ [Plaintext]     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Vector Store   │
                       │   (ChromaDB)     │
                       │ [Encrypted Data] │
                       └──────────────────┘
```

### Security Flow
1. **Encrypted Query**: Client sends AES-GCM encrypted query with metadata
2. **Decryption**: LLM service decrypts query for processing
3. **RAG Processing**: Query processed against encrypted vector store
4. **LLM Generation**: Decrypted query sent to OpenAI for response generation
5. **Encryption**: Response encrypted with same metadata before sending back
6. **Integrity Check**: SHA-256 hashes verify message integrity throughout

## Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional, for containerized deployment)

## Environment Variables

Set the following environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-3.5-turbo"  # Optional, defaults to gpt-3.5-turbo
export OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"  # Optional
export CHUNK_SIZE=1000  # Optional, defaults to 1000
export CHUNK_OVERLAP=200  # Optional, defaults to 200
export MAX_TOKENS=1000  # Optional, defaults to 1000
```

## Installation

### Local Development

1. Clone the repository and navigate to the LLM service directory:
```bash
cd nazarriya-llm
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (see above)

5. Run the service:
```bash
python -m app.main
```

6. Ingest your documents
#### Option A: Using the ingest script
```bash
# Place your documents in the data directory
cp /path/to/your/document1.pdf data/pdfs/
cp /path/to/your/document2.pdf data/pdfs/
cp /path/to/your/document3.pdf data/pdfs/
cp /path/to/your/document.html data/html/

# Run the ingest script
python ingest_documents.py data/pdfs/*.pdf data/html/*.html
```

#### Option B: Using the API directly
```bash
# Ingest documents from file paths
curl -X POST "http://localhost:8001/rag/ingest" \
     -H "Content-Type: application/json" \
     -d '[
       "/full/path/to/document1.pdf",
       "/full/path/to/document2.pdf",
       "/full/path/to/document3.pdf",
       "/full/path/to/document.html"
     ]'
```

6. Test the Encrypted RAG System

```bash
# Test an encrypted query (requires client-side encryption)
curl -X POST "http://localhost:8001/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "encrypted_query": "base64_encoded_encrypted_query",
       "encryption_metadata": {
         "algorithm": "AES-GCM",
         "key_id": "user_key_id",
         "nonce": "base64_encoded_nonce"
       },
       "content_hash": "sha256_hash_of_encrypted_query",
       "encrypted_history": [],
       "max_tokens": 500
     }'
```

7. Test the system
```bash
python test_service.py
```

The service will be available at `http://localhost:8001`

```bash
# Health check
curl http://localhost:8001/health

# RAG system status
curl http://localhost:8001/rag/status

# List documents
curl http://localhost:8001/rag/documents
```

### Docker Deployment

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

2. Or build and run manually:
```bash
docker build -t nazarriya-llm .
docker run -p 8001:8001 -e OPENAI_API_KEY=your-key nazarriya-llm
```

## API Endpoints

### Health Check
- `GET /health` - Basic health check
- `GET /rag/health` - RAG service health check

### Document Management
- `POST /rag/upload` - Upload a document
- `POST /rag/ingest` - Ingest documents from file paths
- `GET /rag/documents` - List all documents
- `DELETE /rag/documents/{filename}` - Delete a document
- `POST /rag/reset` - Reset the entire system

### Encrypted RAG Operations
- `POST /rag/query` - Query the RAG system with encrypted data
- `GET /rag/status` - Get system status

### Dataset Management
- `GET /rag/dataset` - List all dataset items
- `POST /rag/dataset` - Add new dataset item
- `PUT /rag/dataset/{index}` - Update dataset item
- `DELETE /rag/dataset/{index}` - Delete dataset item
- `GET /rag/dataset/category/{category}` - Get dataset by category
- `POST /rag/dataset/ingest` - Ingest entire dataset file
- `DELETE /rag/dataset` - Clear all dataset items

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Usage Examples

### Query the Encrypted RAG System

**Note**: All queries must be encrypted client-side before sending to the API.

```bash
curl -X POST "http://localhost:8001/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "encrypted_query": "base64_encoded_encrypted_query",
       "encryption_metadata": {
         "algorithm": "AES-GCM",
         "key_id": "user_key_id",
         "nonce": "base64_encoded_nonce"
       },
       "content_hash": "sha256_hash_of_encrypted_query",
       "encrypted_history": [],
       "max_tokens": 500
     }'
```

**Response:**
```json
{
  "encrypted_answer": "base64_encoded_encrypted_response",
  "encryption_metadata": {
    "algorithm": "AES-GCM",
    "key_id": "user_key_id",
    "nonce": "base64_encoded_nonce"
  },
  "content_hash": "sha256_hash_of_encrypted_response",
  "sources": [
    {
      "metadata": {
        "source": "document1.pdf"
      }
    }
  ],
  "metadata": {
    "query_length": 256,
    "sources_count": 1,
    "model": "gpt-3.5-turbo",
    "stateless": true
  }
}
```

### Upload a Document

```bash
curl -X POST "http://localhost:8001/rag/upload" \
     -F "file=@document.pdf"
```

### Ingest Documents from Paths

```bash
curl -X POST "http://localhost:8001/rag/ingest" \
     -H "Content-Type: application/json" \
     -d '[
       "/path/to/document1.pdf",
       "/path/to/document2.html"
     ]'
```

### Dataset Management

The service includes a dataset system that provides predefined responses for specific questions, with automatic fallback to document search when no match is found.

#### Add Dataset Item
```bash
curl -X POST "http://localhost:8001/rag/dataset" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How do I deal with family criticism?",
       "answer": "It is important to remember that your worth is not defined by others opinions."
     }'
```

#### Ingest Dataset File
```bash
curl -X POST "http://localhost:8001/rag/dataset/ingest" \
     -H "Content-Type: application/json" \
     -d '{
       "file_path": "sample_dataset.json"
     }'
```

#### Test Dataset Query (Encrypted)
```bash
curl -X POST "http://localhost:8001/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "encrypted_query": "base64_encoded_encrypted_query_about_family_criticism",
       "encryption_metadata": {
         "algorithm": "AES-GCM",
         "key_id": "user_key_id",
         "nonce": "base64_encoded_nonce"
       },
       "content_hash": "sha256_hash_of_encrypted_query",
       "encrypted_history": [],
       "max_tokens": 500
     }'
```

## Document Processing

### Supported Formats
- **PDF**: Uses PyPDF2 for text extraction
- **HTML**: Uses BeautifulSoup for parsing

### Secure Processing Pipeline
1. Document loading and text extraction
2. Text chunking with configurable size and overlap
3. Embedding generation using OpenAI
4. Encrypted vector storage in ChromaDB
5. Encrypted retrieval and response generation
6. End-to-end encryption for all client communications

## Configuration

The service can be configured through environment variables or by modifying `app/config.py`:

### Required Configuration
- `OPENAI_API_KEY`: Required OpenAI API key

### Optional Configuration
- `OPENAI_MODEL`: LLM model (default: gpt-3.5-turbo)
- `OPENAI_EMBEDDING_MODEL`: Embedding model (default: text-embedding-ada-002)
- `CHUNK_SIZE`: Text chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `MAX_TOKENS`: Maximum response tokens (default: 1000)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8001)

### Security Configuration
- All client communications are encrypted using AES-GCM
- Content integrity verified using SHA-256 hashing
- No plaintext data stored or transmitted to clients
- Encryption metadata managed client-side

## Deployment

### Hetzner Deployment

1. **Prepare the server**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Deploy the service**:
```bash
# Clone repository
git clone <your-repo-url>
cd nazarriya-llm

# Set environment variables
export OPENAI_API_KEY="your-key"

# Build and run
docker-compose up -d
```

3. **Configure firewall**:
```bash
sudo ufw allow 8001
sudo ufw enable
```

### Production Considerations

- Use environment-specific configuration files
- Implement proper logging and monitoring (with encrypted data sanitization)
- Set up SSL/TLS certificates for secure communication
- Configure reverse proxy (nginx) with proper security headers
- Implement rate limiting and DDoS protection
- Set up backup strategies for encrypted vector database
- Ensure all client communications use end-to-end encryption
- Regular security audits and dependency updates

## Monitoring and Logging

The service provides:
- Health check endpoints
- Structured logging with encrypted data sanitization
- Error handling and reporting (no sensitive data exposure)
- Performance metrics
- Security event logging

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Ensure `OPENAI_API_KEY` is set correctly
2. **Port Already in Use**: Change the port in configuration or stop conflicting services
3. **Memory Issues**: Reduce chunk size or use smaller models
4. **Vector Store Errors**: Check disk space and permissions
5. **Encryption Errors**: Verify client-side encryption implementation
6. **Content Hash Mismatch**: Ensure proper SHA-256 hashing on client side

### Logs

Check logs for detailed error information:
```bash
# Docker logs
docker-compose logs nazarriya-llm

# Application logs
tail -f logs/app.log
```

## Development

### Project Structure
```
nazarriya-llm/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── services/            # Business logic
│   └── routers/             # API endpoints
├── data/                    # Document storage
├── requirements.txt         # Dependencies
├── Dockerfile              # Container configuration
└── docker-compose.yml      # Local development
```

### Adding New Features

1. Create new service classes in `app/services/`
2. Add Pydantic models in `app/models.py`
3. Create API endpoints in `app/routers/`
4. Update tests and documentation

### Dataset Management

The dataset system can be managed entirely through the API endpoints:

- **Sample Dataset**: `sample_dataset.json` - Template file showing the simplified dataset format (question + answer only)
- **API-First**: All dataset operations are available through REST endpoints
- **Automatic Management**: Keywords, categories, and sources are auto-generated
- **Secure Integration**: Dataset queries are processed through the encrypted RAG pipeline

## License

[Your License Here]

## Support

For issues and questions, please contact [your contact information].
