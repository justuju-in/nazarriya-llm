from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    max_tokens: Optional[int] = 1000


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DocumentUploadResponse(BaseModel):
    message: str
    documents_processed: int
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"


class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    chunks: int
    size_bytes: int
    uploaded_at: str
