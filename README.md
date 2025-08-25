# Nazarriya LLM Service

A RAG-powered LLM service using OpenAI and Langchain, designed to work with the Nazarriya application.

## Features

- **Document Processing**: Support for PDF and HTML documents
- **Vector Storage**: ChromaDB-based vector database for efficient retrieval
- **RAG Pipeline**: Retrieval-Augmented Generation using OpenAI models
- **RESTful API**: FastAPI-based service with comprehensive endpoints
- **Containerized**: Docker support for easy deployment

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main API      │───▶│   LLM Service    │───▶│   OpenAI API    │
│ (nazarriya-api) │    │ (nazarriya-llm) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Vector Store   │
                       │   (ChromaDB)     │
                       └──────────────────┘
```

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

6. Test the RAG System

```bash
# Test a simple query
curl -X POST "http://localhost:8001/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What are the main topics covered in your documents?",
       "query": "What are the main topics covered in your documents?",
       "history": [],
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

### RAG Operations
- `POST /rag/query` - Query the RAG system
- `GET /rag/status` - Get system status

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Usage Examples

### Query the RAG System

```bash
curl -X POST "http://localhost:8001/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is the main topic of the documents?",
       "history": [],
       "max_tokens": 500
     }'
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

## Document Processing

### Supported Formats
- **PDF**: Uses PyPDF2 for text extraction
- **HTML**: Uses BeautifulSoup for parsing

### Processing Pipeline
1. Document loading and text extraction
2. Text chunking with configurable size and overlap
3. Embedding generation using OpenAI
4. Vector storage in ChromaDB
5. Retrieval and response generation

## Configuration

The service can be configured through environment variables or by modifying `app/config.py`:

- `OPENAI_API_KEY`: Required OpenAI API key
- `OPENAI_MODEL`: LLM model (default: gpt-3.5-turbo)
- `OPENAI_EMBEDDING_MODEL`: Embedding model (default: text-embedding-ada-002)
- `CHUNK_SIZE`: Text chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `MAX_TOKENS`: Maximum response tokens (default: 1000)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8001)

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
- Implement proper logging and monitoring
- Set up SSL/TLS certificates
- Configure reverse proxy (nginx)
- Implement rate limiting
- Set up backup strategies for vector database

## Monitoring and Logging

The service provides:
- Health check endpoints
- Structured logging
- Error handling and reporting
- Performance metrics

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Ensure `OPENAI_API_KEY` is set correctly
2. **Port Already in Use**: Change the port in configuration or stop conflicting services
3. **Memory Issues**: Reduce chunk size or use smaller models
4. **Vector Store Errors**: Check disk space and permissions

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

## License

[Your License Here]

## Support

For issues and questions, please contact [your contact information].
